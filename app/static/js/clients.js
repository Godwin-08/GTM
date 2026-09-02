const COULEURS_STATUT_ACTIVITE = {
    actif: 'bg-success/10 text-success',
    inactif: 'bg-warning/10 text-warning',
    aucune: 'bg-gray-100 text-gray-600',
};

// État Alpine de la page /clients : liste, recherche et création par modale.
function pageClientsData() {
    return {
        clients: [],
        chargementEnCours: true,
        erreur: null,
        filtres: {
            q: '',
            secteur: '',
            statut_activite: '',
            tri: '',
        },
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom_entreprise: '', secteur: '', contact_email: '' },
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom_entreprise: '', secteur: '', contact_email: '' },

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.q = params.get('q') || '';
            this.filtres.secteur = params.get('secteur') || '';
            this.filtres.statut_activite = params.get('statut_activite') || '';
            this.filtres.tri = params.get('tri') || '';
        },

        synchroniserUrlNavigateur(reinitialiser = false) {
            if (reinitialiser) {
                if (window.location.search) {
                    window.history.pushState(null, '', window.location.pathname);
                }
                return;
            }
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.secteur && this.filtres.secteur.trim()) {
                params.set('secteur', this.filtres.secteur.trim());
            }
            if (this.filtres.statut_activite) {
                params.set('statut_activite', this.filtres.statut_activite);
            }
            if (this.filtres.tri) {
                params.set('tri', this.filtres.tri);
            }
            const query = params.toString();
            const cible = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            if (window.location.pathname + window.location.search !== cible) {
                window.history.pushState(null, '', cible);
            }
        },

        construireUrlFiltree() {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.secteur && this.filtres.secteur.trim()) {
                params.set('secteur', this.filtres.secteur.trim());
            }
            if (this.filtres.statut_activite) {
                params.set('statut_activite', this.filtres.statut_activite);
            }
            const query = params.toString();
            return query ? `${urlClients}?${query}` : urlClients;
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement clients :', err);
                this.erreur = 'Impossible de charger les clients.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        async appliquerFiltres(gererChargement = true, majHistorique = true) {
            if (gererChargement) this.chargementEnCours = true;
            this.erreur = null;
            if (majHistorique) {
                this.synchroniserUrlNavigateur(false);
            }
            try {
                const res = await fetch(this.construireUrlFiltree());
                const data = await res.json();
                if (!res.ok) throw new Error(data.erreur || 'Réponse serveur invalide');
                this.clients = data;
            } catch (err) {
                console.error('Erreur filtrage clients :', err);
                this.erreur = err.message || 'Impossible de charger les clients.';
                this.clients = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        reinitialiserFiltres() {
            this.filtres = { q: '', secteur: '', statut_activite: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        clientsFiltres() {
            const copie = [...this.clients];
            const t = this.filtres.tri;
            if (t === 'nom_desc') {
                return copie.sort((a, b) => (b.nom_entreprise || '').localeCompare(a.nom_entreprise || '', 'fr'));
            }
            if (t === 'secteur_asc') {
                return copie.sort((a, b) => (a.secteur || '').localeCompare(b.secteur || '', 'fr'));
            }
            if (t === 'statut_asc') {
                const ordre = { actif: 0, inactif: 1, aucune: 2 };
                return copie.sort((a, b) => (ordre[a.statut_activite] ?? 3) - (ordre[b.statut_activite] ?? 3));
            }
            // Par défaut (nom_asc) : nom A → Z
            return copie.sort((a, b) => (a.nom_entreprise || '').localeCompare(b.nom_entreprise || '', 'fr'));
        },

        classeStatut(statut) {
            return COULEURS_STATUT_ACTIVITE[statut] || 'bg-gray-100 text-gray-600';
        },

        ouvrirModaleCreation() {
            this.formulaire = { nom_entreprise: '', secteur: '', contact_email: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlClients, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom_entreprise: this.formulaire.nom_entreprise,
                        secteur: this.formulaire.secteur || null,
                        contact_email: this.formulaire.contact_email || null,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.clients.push({ ...data, nb_participants: data.nb_participants ?? 0 });
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Client créé avec succès.');
            } catch (err) {
                console.error('Erreur création client :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
            }
        },

        ouvrirModaleEdition(client) {
            this.edition = {
                id: client.id,
                nom_entreprise: client.nom_entreprise,
                secteur: client.secteur || '',
                contact_email: client.contact_email || '',
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;

            try {
                const res = await fetch(`${urlClients}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom_entreprise: this.edition.nom_entreprise,
                        secteur: this.edition.secteur || null,
                        contact_email: this.edition.contact_email || null,
                    }),
                });

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Ce nom d\'entreprise est peut-être déjà utilisé, ou une erreur serveur est survenue.' };
                }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                const index = this.clients.findIndex(c => c.id === this.edition.id);
                if (index !== -1) this.clients[index] = { ...data, nb_participants: this.clients[index].nb_participants ?? 0 };
                this.modaleEditionOuverte = false;
            } catch (err) {
                console.error('Erreur modification client :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },
    };
}

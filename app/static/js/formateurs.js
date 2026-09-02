const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

function pageFormateursData() {
    return {
        formateurs: [],
        domaines: [],
        chargementEnCours: true,
        erreur: null,
        filtres: {
            q: '',
            domaine_id: '',
            type: '',
            tri: '',
        },
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' },
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom: '', domaine_id: '', email: '', telephone: '', a_un_compte: false },

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.q = params.get('q') || '';
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.type = params.get('type') || '';
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
            if (this.filtres.domaine_id) {
                params.set('domaine_id', this.filtres.domaine_id);
            }
            if (this.filtres.type) {
                params.set('type', this.filtres.type);
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
            if (this.filtres.domaine_id) {
                params.set('domaine_id', this.filtres.domaine_id);
            }
            if (this.filtres.type) {
                params.set('type', this.filtres.type);
            }
            const query = params.toString();
            return query ? `${urlFormateurs}?${query}` : urlFormateurs;
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const domainesRes = await fetch(urlDomaines);
                if (domainesRes.ok) {
                    this.domaines = await domainesRes.json();
                }
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement formateurs :', err);
                this.erreur = 'Impossible de charger les formateurs.';
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
                this.formateurs = data;
            } catch (err) {
                console.error('Erreur filtrage formateurs :', err);
                this.erreur = err.message || 'Impossible de charger les formateurs.';
                this.formateurs = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        reinitialiserFiltres() {
            this.filtres = { q: '', domaine_id: '', type: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        formateursFiltres() {
            const copie = [...this.formateurs];
            const t = this.filtres.tri;
            if (t === 'nom_desc') return copie.sort((a, b) => b.nom.localeCompare(a.nom));
            if (t === 'domaine_asc') return copie.sort((a, b) => (a.domaine?.nom || '').localeCompare(b.domaine?.nom || ''));
            // Par défaut : nom A-Z (nom_asc)
            return copie.sort((a, b) => a.nom.localeCompare(b.nom));
        },

        nomDomaine(formateur) {
            return formateur.domaine?.nom || '';
        },

        couleurDomaine(nomDomaine) {
            return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600';
        },

        ouvrirModaleCreation() {
            this.formulaire = { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlFormateurs, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.formulaire.nom,
                        domaine_id: this.formulaire.domaine_id,
                        email: this.formulaire.email || null,
                        telephone: this.formulaire.telephone || null,
                        ...(this.formulaire.utilisateur_id ? { utilisateur_id: this.formulaire.utilisateur_id } : {}),
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formateur créé avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur création formateur :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
            }
        },

        ouvrirModaleEdition(formateur) {
            this.edition = {
                id: formateur.id,
                nom: formateur.nom,
                domaine_id: formateur.domaine?.id ?? '',
                email: formateur.email || '',
                telephone: formateur.telephone || '',
                a_un_compte: formateur.a_un_compte,
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlFormateurs}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.edition.nom,
                        domaine_id: this.edition.domaine_id,
                        email: this.edition.email || null,
                        telephone: this.edition.telephone || null,
                    }),
                });

                let data;
                try { data = await res.json(); } catch { data = { erreur: 'Erreur inattendue du serveur.' }; }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurEdition);
                    return;
                }

                this.modaleEditionOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formateur modifié avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur modification formateur :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },
    };
}

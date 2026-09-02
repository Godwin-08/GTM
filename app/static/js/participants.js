function pageParticipantsData() {
    return {
        participants: [],
        clients: [],
        chargementEnCours: true,
        erreur: null,
        filtres: {
            q: '',
            client_id: '',
            tri: '',
        },
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom: '', email: '', client_id: '' },
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom: '', email: '', client_id: '' },

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.q = params.get('q') || '';
            this.filtres.client_id = params.get('client_id') || '';
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
            if (this.filtres.client_id) {
                params.set('client_id', this.filtres.client_id);
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
            if (this.filtres.client_id) {
                params.set('client_id', this.filtres.client_id);
            }
            const query = params.toString();
            return query ? `${urlParticipants}?${query}` : urlParticipants;
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const clientsRes = await fetch(urlClients);
                if (clientsRes.ok) {
                    this.clients = await clientsRes.json();
                }
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement participants :', err);
                this.erreur = 'Impossible de charger les participants.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
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
                this.participants = data;
            } catch (err) {
                console.error('Erreur filtrage participants :', err);
                this.erreur = err.message || 'Impossible de charger les participants.';
                this.participants = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        reinitialiserFiltres() {
            this.filtres = { q: '', client_id: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        participantsFiltres() {
            const copie = [...this.participants];
            const t = this.filtres.tri;
            if (t === 'nom_desc') {
                return copie.sort((a, b) => (b.nom || '').localeCompare(a.nom || '', 'fr'));
            }
            if (t === 'entreprise_asc') {
                return copie.sort((a, b) => (a.client?.nom_entreprise || '').localeCompare(b.client?.nom_entreprise || '', 'fr'));
            }
            // Par défaut (nom_asc) : nom A → Z
            return copie.sort((a, b) => (a.nom || '').localeCompare(b.nom || '', 'fr'));
        },

        ouvrirModaleCreation() {
            this.formulaire = { nom: '', email: '', client_id: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleCreation() { if (!this.envoiEnCours) this.modaleOuverte = false; },
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlParticipants, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({ nom: this.formulaire.nom, email: this.formulaire.email, client_id: this.formulaire.client_id }),
                });
                const data = await res.json();
                if (!res.ok) { this.erreurFormulaire = data.erreur || 'Une erreur est survenue.'; if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire); return; }
                this.participants.push(data);
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Participant créé avec succès.');
            } catch (err) {
                console.error('Erreur création participant :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally { this.envoiEnCours = false; }
        },

        ouvrirModaleEdition(participant) {
            this.edition = {
                id: participant.id,
                nom: participant.nom,
                email: participant.email,
                client_id: participant.client?.id ?? '',
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleEdition() { if (!this.editionEnCours) this.modaleEditionOuverte = false; },
        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlParticipants}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.edition.nom,
                        email: this.edition.email,
                        client_id: this.edition.client_id,
                    }),
                });

                let data;
                try { data = await res.json(); } catch { data = { erreur: 'Cet email est peut-être déjà utilisé, ou une erreur serveur est survenue.' }; }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                const index = this.participants.findIndex(p => p.id === this.edition.id);
                if (index !== -1) this.participants[index] = data;
                this.modaleEditionOuverte = false;
            } catch (err) {
                console.error('Erreur modification participant :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally { this.editionEnCours = false; }
        },
    };
}

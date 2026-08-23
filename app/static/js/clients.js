// État Alpine de la page /clients : liste, recherche et création par modale.
function pageClientsData() {
    return {
        clients: [],
        recherche: '',
        chargementEnCours: true,
        erreur: null,
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom_entreprise: '', secteur: '', contact_email: '' },
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom_entreprise: '', secteur: '', contact_email: '' },

        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        ouvrirModaleSuppression(client) {
            this.aSupprimer = client;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        fermerModaleSuppression() {
            if (!this.suppressionEnCours) {
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;
            }
        },

        async confirmerSuppression() {
            this.suppressionEnCours = true;
            this.erreurSuppression = null;

            try {
                const res = await fetch(`${urlClients}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (res.status === 204) {
                    this.clients = this.clients.filter(c => c.id !== this.aSupprimer.id);
                    this.modaleSuppressionOuverte = false;
                    this.aSupprimer = null;
                    return;
                }

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Erreur inattendue du serveur.' };
                }
                this.erreurSuppression = data.erreur || 'Impossible de supprimer ce client.';

            } catch (err) {
                console.error('Erreur suppression client :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const res = await fetch(urlClients);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                this.clients = await res.json();
            } catch (err) {
                console.error('Erreur chargement clients :', err);
                this.erreur = 'Impossible de charger les clients.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        clientsFiltres() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            return this.clients
                .filter(client => {
                    const entreprise = (client.nom_entreprise || '').toLocaleLowerCase();
                    const secteur = (client.secteur || '').toLocaleLowerCase();
                    return !rechercheMin || entreprise.includes(rechercheMin) || secteur.includes(rechercheMin);
                })
                .sort((a, b) => (b.nb_participants || 0) - (a.nb_participants || 0));
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
                    return;
                }
                this.clients.push({ ...data, nb_participants: data.nb_participants ?? 0 });
                this.modaleOuverte = false;
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

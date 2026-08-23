function pageParticipantsData() {
    return {
        participants: [], clients: [], recherche: '', filtreEntreprise: '', chargementEnCours: true, erreur: null,
        modaleOuverte: false, envoiEnCours: false, erreurFormulaire: null,
        formulaire: { nom: '', email: '', client_id: '' },
        modaleEditionOuverte: false, editionEnCours: false, erreurEdition: null,
        edition: { id: null, nom: '', email: '', client_id: '' },

        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        ouvrirModaleSuppression(participant) {
            this.aSupprimer = participant;
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
                const res = await fetch(`${urlParticipants}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (res.status === 204) {
                    this.participants = this.participants.filter(p => p.id !== this.aSupprimer.id);
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
                this.erreurSuppression = data.erreur || 'Impossible de supprimer ce participant.';

            } catch (err) {
                console.error('Erreur suppression participant :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const [participantsRes, clientsRes] = await Promise.all([fetch(urlParticipants), fetch(urlClients)]);
                if (!participantsRes.ok) throw new Error('Réponse serveur invalide');
                this.participants = await participantsRes.json();
                if (clientsRes.ok) this.clients = await clientsRes.json();
            } catch (err) {
                console.error('Erreur chargement participants :', err);
                this.erreur = 'Impossible de charger les participants.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        nomEntreprise(participant) { return participant.client?.nom_entreprise || ''; },
        participantsFiltres() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            return this.participants.filter(participant => {
                const entreprise = this.nomEntreprise(participant);
                const nom = (participant.nom || '').toLocaleLowerCase();
                const email = (participant.email || '').toLocaleLowerCase();
                return (!this.filtreEntreprise || entreprise === this.filtreEntreprise)
                    && (!rechercheMin || nom.includes(rechercheMin) || email.includes(rechercheMin));
            }).sort((a, b) => (a.nom || '').localeCompare(b.nom || '', 'fr'));
        },
        entreprisesDisponibles() { return this.clients.map(client => client.nom_entreprise).sort((a, b) => a.localeCompare(b, 'fr')); },

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
                if (!res.ok) { this.erreurFormulaire = data.erreur || 'Une erreur est survenue.'; return; }
                this.participants.push(data);
                this.modaleOuverte = false;
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

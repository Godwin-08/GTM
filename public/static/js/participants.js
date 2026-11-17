function pageParticipantsData() {
    return {
        participants: [],
        clients: [],
        selectionnees: [], bloquees: [],
        modeSelection: false,
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

        // --- État de la modale de suppression ---
        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        // --- État de la modale d'import par lot (Point 8) ---
        modaleImportOuverte: false,
        importEnCours: false,
        fichierImport: null,
        nomFichierImport: '',
        dragOver: false,
        rapportImport: null,
        erreurImport: null,

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

        urlExport(format = 'csv') {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) params.set('q', this.filtres.q.trim());
            if (this.filtres.client_id) params.set('client_id', this.filtres.client_id);
            const qs = params.toString();
            return `/api/participants/export/${format}${qs ? '?' + qs : ''}`;
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

        basculerModeSelection() {
            this.modeSelection = !this.modeSelection;
            this.selectionnees = [];
            this.bloquees = [];
        },

        toggleSelection(id) {
            if (this.selectionnees.includes(id)) {
                this.selectionnees = this.selectionnees.filter(item => item !== id);
            } else {
                this.selectionnees = [...this.selectionnees, id];
            }
        },

        toggleSelectionGlobale() {
            const visibles = this.participantsFiltres().map(participant => participant.id);
            const tousVisiblesSelectionnes = visibles.length > 0 && visibles.every(id => this.selectionnees.includes(id));
            if (tousVisiblesSelectionnes) {
                this.selectionnees = this.selectionnees.filter(id => !visibles.includes(id));
            } else {
                this.selectionnees = [...new Set([...this.selectionnees, ...visibles])];
            }
        },

        async supprimerSelection() {
            if (this.selectionnees.length === 0) return;
            const ok = await window.demanderConfirmation(
                `${this.selectionnees.length} participant(s) sélectionné(s) seront définitivement supprimé(s).`
            );
            if (!ok) return;

            try {
                const res = await fetch(urlParticipants, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ ids: this.selectionnees }),
                });
                const data = await res.json().catch(() => ({}));
                this.bloquees = data.bloquees || [];
                if (!res.ok) {
                    if (this.bloquees.length) {
                        const bloque = this.participants.find(participant => participant.id === this.bloquees[0].id) || {};
                        this.aSupprimer = { ...bloque, id: this.bloquees[0].id, client_id: this.bloquees[0].client_id };
                        this.erreurSuppression = data.erreur || 'Ce participant possède encore des inscriptions.';
                        this.modaleSuppressionOuverte = true;
                        this.$nextTick(() => lucide.createIcons());
                        return;
                    }
                    throw new Error(data.erreur || 'Impossible de supprimer les participants sélectionnés.');
                }

                const supprimees = data.supprimees || [];
                const bloquees = data.bloquees || [];
                this.participants = this.participants.filter(participant => !supprimees.includes(participant.id));
                this.selectionnees = bloquees.map(participant => participant.id);
                if (typeof window.afficherToast === 'function') {
                    if (bloquees.length) {
                        const bloque = this.participants.find(participant => participant.id === bloquees[0].id) || {};
                        this.aSupprimer = { ...bloque, id: bloquees[0].id, client_id: bloquees[0].client_id };
                        this.erreurSuppression = `${supprimees.length} participant(s) supprimé(s). ${bloquees.length} participant(s) conservé(s) car ils ont des inscriptions.`;
                        this.modaleSuppressionOuverte = true;
                        this.$nextTick(() => lucide.createIcons());
                    } else {
                        window.afficherToast('succes', `${supprimees.length} participant(s) supprimé(s).`);
                    }
                }
            } catch (err) {
                console.error('Erreur suppression sélection participants :', err);
                if (typeof window.afficherToast === 'function') window.afficherToast('erreur', err.message);
                else alert(err.message);
            }
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

        /**
         * Ouvre la modale de confirmation de suppression pour un participant.
         * @param {object} participant
         */
        ouvrirModaleSuppression(participant) {
            this.aSupprimer = participant;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        /**
         * Ferme la modale de suppression si aucune opération n'est en cours.
         */
        fermerModaleSuppression() {
            if (!this.suppressionEnCours) {
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;
                this.erreurSuppression = null;
            }
        },

        /**
         * Confirme et exécute la suppression du participant via DELETE /api/participants/<id>.
         */
        async confirmerSuppression() {
            if (!this.aSupprimer) return;
            this.suppressionEnCours = true;
            this.erreurSuppression = null;

            try {
                const res = await fetch(`${urlParticipants}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                });

                if (!res.ok) {
                    let errData = {};
                    try {
                        errData = await res.json();
                    } catch {}
                    this.erreurSuppression = errData.erreur || 'Erreur lors de la suppression du participant.';
                    if (typeof window.afficherToast === 'function') {
                        window.afficherToast('erreur', this.erreurSuppression);
                    }
                    return;
                }

                const nomSupprime = this.aSupprimer.nom;
                this.participants = this.participants.filter(p => p.id !== this.aSupprimer.id);
                this.selectionnees = this.selectionnees.filter(id => id !== this.aSupprimer.id);
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;

                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('succes', `Participant "${nomSupprime}" supprimé avec succès.`);
                }
            } catch (err) {
                console.error('Erreur suppression participant :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        // =========================================================================
        // Méthodes d'Import par Lot (Point 8)
        // =========================================================================

        ouvrirModaleImport() {
            this.reinitialiserImport();
            this.modaleImportOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        fermerModaleImport() {
            if (!this.importEnCours) {
                this.modaleImportOuverte = false;
                this.reinitialiserImport();
            }
        },

        reinitialiserImport() {
            this.fichierImport = null;
            this.nomFichierImport = '';
            this.rapportImport = null;
            this.erreurImport = null;
            this.importEnCours = false;
            this.dragOver = false;
            const input = document.getElementById('fichier-import-participants');
            if (input) input.value = '';
        },

        fichierSelectionne(event) {
            const files = event.target.files || (event.dataTransfer && event.dataTransfer.files);
            if (files && files.length > 0) {
                const f = files[0];
                const nomLower = f.name.toLowerCase();
                if (!nomLower.endsWith('.csv') && !nomLower.endsWith('.xlsx')) {
                    this.erreurImport = 'Format non supporté. Veuillez choisir un fichier .csv ou .xlsx.';
                    return;
                }
                this.fichierImport = f;
                this.nomFichierImport = f.name;
                this.erreurImport = null;
                this.rapportImport = null;
            }
        },

        async soumettreImport() {
            if (!this.fichierImport) {
                this.erreurImport = 'Veuillez sélectionner un fichier à importer.';
                return;
            }

            this.importEnCours = true;
            this.erreurImport = null;
            this.rapportImport = null;

            const formData = new FormData();
            formData.append('fichier', this.fichierImport);

            try {
                const res = await fetch('/api/participants/import', {
                    method: 'POST',
                    credentials: 'include',
                    body: formData,
                });

                const data = await res.json();
                if (!res.ok) {
                    this.erreurImport = data.erreur || 'Erreur lors du traitement de l\'import.';
                    return;
                }

                this.rapportImport = data;

                if (data.nb_importes > 0) {
                    if (typeof window.afficherToast === 'function') {
                        window.afficherToast('succes', `${data.nb_importes} participant(s) importé(s) avec succès.`);
                    }
                    // Rafraîchir la liste sans fermer immédiatement pour laisser l'utilisateur voir le compte-rendu
                    await this.appliquerFiltres(false, false);
                }
            } catch (err) {
                console.error('Erreur import participants :', err);
                this.erreurImport = 'Impossible de contacter le serveur pour l\'import.';
            } finally {
                this.importEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },
    };
}

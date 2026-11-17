/**
 * @file client_detail.js
 * @description Composant Alpine.js pour la page de détail d'un client entreprise (/clients/<id>).
 * Charge en parallèle les informations du client et la liste de ses participants.
 * Fournit les helpers de mise en forme visuelle des badges de statut de session.
 */

// ============================================================
// Page /clients/<id> : détail complet d'un client,
// avec la liste de ses participants.
// ============================================================

/**
 * Composant Alpine.js pour la fiche de détail d'un client.
 * @param {number} clientId Identifiant unique du client passé depuis le template Jinja.
 * @returns {object} État réactif et méthodes de la page.
 */
function pageClientDetailData(clientId) {
    return {
        /** @type {object|null} Données complètes du client (nom, secteur, contact…) */
        client: null,

        /** @type {Array} Participants appartenant à cette entreprise cliente */
        participants: [],
        modeSelection: false,
        selectionnees: [],
        suppressionEnCours: false,

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur éventuel */
        erreur: null,

        /**
         * Charge en parallèle le détail du client et la liste de ses participants.
         * Utilise Promise.all pour optimiser les temps de réponse.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const [resClient, resParticipants] = await Promise.all([
                    fetch(`/api/clients/${clientId}`),
                    fetch(`/api/participants?client_id=${clientId}`),
                ]);

                if (!resClient.ok) throw new Error('Client introuvable');
                this.client = await resClient.json();

                if (resParticipants.ok) {
                    this.participants = await resParticipants.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail client :', err);
                this.erreur = 'Impossible de charger ce client.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        /**
         * Renvoie les classes CSS du badge de statut d'une session affichée dans la fiche.
         * @param {string} statut Statut technique de la session ('planifiee', 'en_cours', 'terminee', 'annulee').
         * @returns {string} Classes Tailwind CSS.
         */
        couleurStatutSession(statut) {
            const COULEURS = {
                planifiee: 'bg-info/10 text-info',
                en_cours: 'bg-warning/10 text-warning',
                terminee: 'bg-success/10 text-success',
                annulee: 'bg-gray-100 text-gray-600',
            };
            return COULEURS[statut] || 'bg-gray-100 text-gray-600';
        },

        /**
         * Renvoie le libellé français lisible pour un statut de session.
         * @param {string} statut Statut technique.
         * @returns {string}
         */
        labelStatutSession(statut) {
            const LABELS = {
                planifiee: 'Planifiée',
                en_cours: 'En cours',
                terminee: 'Terminée',
                annulee: 'Annulée',
            };
            return LABELS[statut] || statut;
        },

        toggleSelection(id) {
            this.selectionnees = this.selectionnees.includes(id)
                ? this.selectionnees.filter(item => item !== id)
                : [...this.selectionnees, id];
        },

        toggleSelectionGlobale() {
            const ids = this.participants.map(participant => participant.id);
            const tousSelectionnes = ids.length > 0 && ids.every(id => this.selectionnees.includes(id));
            this.selectionnees = tousSelectionnes ? [] : ids;
        },

        async supprimerSelection() {
            if (!this.selectionnees.length || !await window.demanderConfirmation(`${this.selectionnees.length} participant(s) sélectionné(s) seront définitivement supprimé(s).`)) return;
            this.suppressionEnCours = true;
            try {
                const res = await fetch('/api/participants', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ ids: this.selectionnees }),
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.erreur || 'Impossible de supprimer les participants sélectionnés.');
                this.participants = this.participants.filter(participant => !this.selectionnees.includes(participant.id));
                this.selectionnees = [];
                window.afficherToast?.('succes', `${data.supprimees?.length || 0} participant(s) supprimé(s).`);
            } catch (err) {
                window.afficherToast?.('erreur', err.message || 'Erreur lors de la suppression.');
            } finally {
                this.suppressionEnCours = false;
            }
        },
    };
}

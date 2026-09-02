// ============================================================
// Page /clients/<id> : détail complet d'un client,
// avec la liste de ses participants.
// ============================================================

function pageClientDetailData(clientId) {
    return {
        client: null,
        participants: [],
        chargementEnCours: true,
        erreur: null,

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

        couleurStatutSession(statut) {
            const COULEURS = {
                planifiee: 'bg-info/10 text-info',
                en_cours: 'bg-warning/10 text-warning',
                terminee: 'bg-success/10 text-success',
                annulee: 'bg-gray-100 text-gray-600',
            };
            return COULEURS[statut] || 'bg-gray-100 text-gray-600';
        },

        labelStatutSession(statut) {
            const LABELS = {
                planifiee: 'Planifiée',
                en_cours: 'En cours',
                terminee: 'Terminée',
                annulee: 'Annulée',
            };
            return LABELS[statut] || statut;
        },
    };
}


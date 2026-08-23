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
    };
}


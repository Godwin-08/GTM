// ============================================================
// Affiche les "Points d'attention" du dashboard.
// Consomme l'endpoint backend `/api/stats/points-attention`.
// Le backend centralise désormais l'ensemble des règles métier.
// ============================================================

function pointsAttentionData() {
    return {
        total: 0,
        items: [],
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const res = await fetch(urlPointsAttention);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                const data = await res.json();

                this.total = data.total || 0;
                this.items = data.items || [];
            } catch (err) {
                console.error('Erreur chargement points d\'attention :', err);
                this.erreur = 'Impossible de charger les points d\'attention.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        couleurPastille(niveau) {
            if (niveau === 'danger') return 'bg-danger';
            if (niveau === 'warning') return 'bg-warning';
            if (niveau === 'info') return 'bg-success';
            return 'bg-gray-400';
        },
    };
}

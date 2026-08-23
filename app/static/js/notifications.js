// ============================================================
// Page /notifications : vue complète des points d'attention,
// avec filtres par niveau (risque/opportunité/tendance).
// Consomme la même route backend que la cloche, aucune
// logique de calcul dupliquée ici.
// ============================================================

function pageNotificationsData() {
    return {
        items: [],
        filtreNiveau: '',
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const res = await fetch(urlPointsAttention);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                const data = await res.json();
                this.items = data.items;
            } catch (err) {
                console.error('Erreur chargement notifications :', err);
                this.erreur = 'Impossible de charger les notifications.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        itemsFiltres() {
            if (!this.filtreNiveau) return this.items;
            return this.items.filter(i => i.niveau === this.filtreNiveau);
        },

        couleurNiveau(niveau) {
            const couleurs = { danger: 'bg-danger', warning: 'bg-warning', info: 'bg-gray-400' };
            return couleurs[niveau] || 'bg-gray-400';
        },
    };
}


// ============================================================
// Page /utilisateurs/<id> : détail d'un compte utilisateur,
// avec statut, rôle, et fiche Formateur associée si existante.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const ROLES_LABELS = {
    'admin': 'Administrateur',
    'gestionnaire': 'Gestionnaire',
    'formateur': 'Formateur',
};

function pageUtilisateurDetailData(utilisateurId) {
    return {
        utilisateur: null,
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const res = await fetch(`/api/utilisateurs/${utilisateurId}`);
                if (!res.ok) throw new Error('Compte utilisateur introuvable');
                this.utilisateur = await res.json();
            } catch (err) {
                console.error('Erreur chargement détail utilisateur :', err);
                this.erreur = 'Impossible de charger ce compte utilisateur.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        formaterDate(dateStr) {
            if (!dateStr) return '—';
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]} ${d.getFullYear()}`;
        },

        labelRole(roleNom) {
            return ROLES_LABELS[roleNom] || roleNom;
        },

        initiales(nom) {
            if (!nom) return 'U';
            const parts = nom.trim().split(/\s+/);
            if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
            return nom.substring(0, 2).toUpperCase();
        },
    };
}


// ============================================================
// Page /sessions/<id> : détail complet d'une session,
// avec la liste de ses inscrits.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const COULEURS_STATUT_SESSION = {
    'planifiee': { classe: 'bg-info/10 text-info', label: 'Planifiée' },
    'en_cours': { classe: 'bg-warning/10 text-warning', label: 'En cours' },
    'terminee': { classe: 'bg-success/10 text-success', label: 'Terminée' },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

const COULEURS_STATUT_INSCRIPTION = {
    'confirmee': { classe: 'bg-success/10 text-success', label: 'Confirmée' },
    'liste_attente': { classe: 'bg-warning/10 text-warning', label: "Liste d'attente" },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

// sessionId est passé depuis Jinja au moment de l'appel : x-data="pageSessionDetailData({{ session_id }})"
function pageSessionDetailData(sessionId) {
    return {
        session: null,
        inscriptions: [],
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                // Deux appels indépendants : le détail de la session, et ses inscriptions
                const [resSession, resInscriptions] = await Promise.all([
                    fetch(`/api/sessions/${sessionId}`),
                    fetch(`/api/inscriptions?session_id=${sessionId}`),
                ]);

                if (!resSession.ok) throw new Error('Session introuvable');
                this.session = await resSession.json();

                // Les inscriptions ne sont pas critiques pour afficher la session elle-même :
                // si cet appel échoue, on affiche quand même la session avec une liste vide
                if (resInscriptions.ok) {
                    this.inscriptions = await resInscriptions.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail session :', err);
                this.erreur = 'Impossible de charger cette session.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        formaterDate(dateStr) {
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]} ${d.getFullYear()}`;
        },

        labelStatut(statut) {
            return (COULEURS_STATUT_SESSION[statut] || { label: statut }).label;
        },
        classeBadgeStatut(statut) {
            return (COULEURS_STATUT_SESSION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },

        labelInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { label: statut }).label;
        },
        classeBadgeInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },
    };
}


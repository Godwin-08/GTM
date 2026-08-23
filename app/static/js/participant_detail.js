// ============================================================
// Page /participants/<id> : détail d'un participant,
// avec la liste de ses inscriptions aux sessions.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const COULEURS_STATUT_INSCRIPTION = {
    'confirmee': { classe: 'bg-success/10 text-success', label: 'Confirmée' },
    'liste_attente': { classe: 'bg-warning/10 text-warning', label: "Liste d'attente" },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

function pageParticipantDetailData(participantId) {
    return {
        participant: null,
        inscriptions: [],
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const [resParticipant, resInscriptions] = await Promise.all([
                    fetch(`/api/participants/${participantId}`),
                    fetch(`/api/inscriptions?participant_id=${participantId}`),
                ]);

                if (!resParticipant.ok) throw new Error('Participant introuvable');
                this.participant = await resParticipant.json();

                if (resInscriptions.ok) {
                    this.inscriptions = await resInscriptions.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail participant :', err);
                this.erreur = 'Impossible de charger ce participant.';
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

        labelInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { label: statut }).label;
        },
        classeBadgeInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },
    };
}


// ============================================================
// Page /formations/<id> : détail d'une formation,
// avec la liste de ses sessions (passées et à venir).
// Chaque ligne de session est cliquable et mène à son détail.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

const COULEURS_STATUT = {
    'planifiee': { classe: 'bg-info/10 text-info', label: 'Planifiée' },
    'en_cours': { classe: 'bg-warning/10 text-warning', label: 'En cours' },
    'terminee': { classe: 'bg-success/10 text-success', label: 'Terminée' },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

function pageFormationDetailData(formationId) {
    return {
        formation: null,
        sessions: [],
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const [resFormation, resSessions] = await Promise.all([
                    fetch(`/api/formations/${formationId}`),
                    fetch(`/api/sessions?formation_id=${formationId}`),
                ]);

                if (!resFormation.ok) throw new Error('Formation introuvable');
                this.formation = await resFormation.json();

                if (resSessions.ok) {
                    this.sessions = await resSessions.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail formation :', err);
                this.erreur = 'Impossible de charger cette formation.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        // Les sessions les plus récentes/à venir en premier
        sessionsTriees() {
            return [...this.sessions].sort((a, b) => new Date(b.date_debut) - new Date(a.date_debut));
        },

        formaterDate(dateStr) {
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]}`;
        },

        couleurDomaine(nomDomaine) {
            return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600';
        },

        labelStatut(statut) {
            return (COULEURS_STATUT[statut] || { label: statut }).label;
        },
        classeBadgeStatut(statut) {
            return (COULEURS_STATUT[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },

        classeBadgeRemplissage(s) {
            if (s.taux_remplissage >= 0.7) return 'bg-success/10 text-success';
            if (s.taux_remplissage >= 0.4) return 'bg-warning/10 text-warning';
            return 'bg-danger/10 text-danger';
        },
    };
}


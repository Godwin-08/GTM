/**
 * @file formation_detail.js
 * @description Composant Alpine.js pour la page de détail d'une formation (/formations/<id>).
 * Charge en parallèle les informations de la formation et toutes ses sessions associées.
 * Fournit les helpers de tri, formatage de dates et mise en forme visuelle des badges.
 */

// ============================================================
// Page /formations/<id> : détail d'une formation,
// avec la liste de ses sessions (passées et à venir).
// Chaque ligne de session est cliquable et mène à son détail.
// ============================================================

/** @type {string[]} Abréviations françaises des mois pour l'affichage des dates */
const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

/** @type {Object<string, string>} Correspondance domaine → classes CSS Tailwind pour les badges */
const COULEURS_DOMAINE = {
    'Web & Data': 'bg-blue-50 text-blue-700 border border-blue-200/80',
    'Management Agile': 'bg-amber-50 text-amber-800 border border-amber-200/80',
    'Cybersécurité': 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
};

/** @type {Object<string, {classe: string, label: string}>} Configuration visuelle des statuts de session */
const COULEURS_STATUT = {
    'planifiee': { classe: 'bg-info/10 text-info', label: 'Planifiée' },
    'en_cours': { classe: 'bg-warning/10 text-warning', label: 'En cours' },
    'terminee': { classe: 'bg-success/10 text-success', label: 'Terminée' },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

/**
 * Composant Alpine.js pour la fiche de détail d'une formation.
 * @param {number} formationId Identifiant unique de la formation passé depuis le template Jinja.
 * @returns {object} État réactif et méthodes de la page.
 */
function pageFormationDetailData(formationId) {
    return {
        /** @type {object|null} Données de la formation (titre, domaine, durée, description) */
        formation: null,

        /** @type {Array} Sessions associées à cette formation */
        sessions: [],

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur éventuel */
        erreur: null,

        /**
         * Charge en parallèle le détail de la formation et sa liste de sessions.
         * @returns {Promise<void>}
         */
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

        /**
         * Renvoie les sessions triées avec les plus récentes/à venir en premier (ordre décroissant).
         * @returns {Array}
         */
        sessionsTriees() {
            return [...this.sessions].sort((a, b) => new Date(b.date_debut) - new Date(a.date_debut));
        },

        /**
         * Formate une date ISO en libellé court "J Mois".
         * @param {string} dateStr Date au format ISO 8601.
         * @returns {string} Ex : "13 Sept."
         */
        formaterDate(dateStr) {
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]}`;
        },

        /**
         * Renvoie les classes CSS du badge de domaine.
         * @param {string} nomDomaine Nom du domaine.
         * @returns {string}
         */
        couleurDomaine(nomDomaine) {
            return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600';
        },

        /**
         * Renvoie le libellé français lisible pour un statut de session.
         * @param {string} statut Statut technique.
         * @returns {string}
         */
        labelStatut(statut) {
            return (COULEURS_STATUT[statut] || { label: statut }).label;
        },

        /**
         * Renvoie les classes CSS du badge de statut de session.
         * @param {string} statut Statut technique.
         * @returns {string}
         */
        classeBadgeStatut(statut) {
            return (COULEURS_STATUT[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },

        /**
         * Renvoie les classes CSS du badge de taux de remplissage d'une session.
         * @param {object} s Objet session avec la propriété taux_remplissage (entre 0 et 1).
         * @returns {string}
         */
        classeBadgeRemplissage(s) {
            if (s.taux_remplissage >= 0.7) return 'bg-success/10 text-success';
            if (s.taux_remplissage >= 0.4) return 'bg-warning/10 text-warning';
            return 'bg-danger/10 text-danger';
        },
    };
}

/**
 * @file inscriptions.js
 * @description Composant Alpine.js pour la page liste des inscriptions (/inscriptions).
 * Gère un filtrage multicritère avancé (session, formation, client, participant, statut, dates),
 * la synchronisation URL, les exports CSV/XLSX, et la validation côté client des bornes de dates.
 */

/** @type {Object<string, string>} Correspondance statut d'inscription → classes CSS Tailwind */
const COULEURS_STATUT_INSCRIPTION = {
    confirmee: 'bg-success/10 text-success',
    annulee: 'bg-gray-100 text-gray-600',
    liste_attente: 'bg-warning/10 text-warning',
};

/**
 * Composant Alpine.js pour la page liste des inscriptions.
 * @returns {object} État réactif et méthodes de la page.
 */
function pageInscriptionsData() {
    return {
        /** @type {Array} Inscriptions chargées depuis l'API selon les filtres actifs */
        inscriptions: [],

        // Référentiels chargés pour alimenter les sélecteurs de filtres
        sessions: [],
        formations: [],
        clients: [],
        participants: [],

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur éventuel */
        erreur: null,

        /**
         * Critères de filtrage actifs.
         * @type {{statut: string, session_id: string, formation_id: string, client_id: string, participant_id: string, date_debut_min: string, date_debut_max: string}}
         */
        filtres: {
            statut: '',
            session_id: '',
            formation_id: '',
            client_id: '',
            participant_id: '',
            date_debut_min: '',
            date_debut_max: '',
        },

        /**
         * Enregistre les réactivités et l'écouteur popstate pour la navigation navigateur.
         */
        init() {
            this.$watch('inscriptions', () => {
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            });
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        /**
         * Lit les paramètres GET de l'URL courante et hydrate l'état des filtres.
         */
        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.statut = params.get('statut') || '';
            this.filtres.formation_id = params.get('formation_id') || '';
            this.filtres.session_id = params.get('session_id') || '';
            this.filtres.client_id = params.get('client_id') || '';
            this.filtres.participant_id = params.get('participant_id') || '';
            this.filtres.date_debut_min = params.get('date_debut_min') || '';
            this.filtres.date_debut_max = params.get('date_debut_max') || '';
        },

        /**
         * Écrit les filtres actifs dans l'URL du navigateur via History API.
         * @param {boolean} reinitialiser Si vrai, efface tous les paramètres.
         */
        synchroniserUrlNavigateur(reinitialiser = false) {
            if (reinitialiser) {
                if (window.location.search) {
                    window.history.pushState(null, '', window.location.pathname);
                }
                return;
            }
            const params = new URLSearchParams();
            // Écriture dynamique de tous les filtres non vides
            Object.entries(this.filtres).forEach(([cle, valeur]) => {
                if (valeur !== '' && valeur !== null && valeur !== undefined) {
                    params.set(cle, valeur);
                }
            });
            const query = params.toString();
            const cible = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            if (window.location.pathname + window.location.search !== cible) {
                window.history.pushState(null, '', cible);
            }
        },

        /**
         * Construit l'URL d'export (CSV ou XLSX) avec les filtres actifs.
         * @param {'csv'|'xlsx'} format Format souhaité.
         * @returns {string}
         */
        urlExport(format = 'csv') {
            const params = new URLSearchParams();
            Object.entries(this.filtres).forEach(([cle, valeur]) => {
                if (valeur !== '' && valeur !== null && valeur !== undefined) {
                    params.set(cle, valeur);
                }
            });
            const qs = params.toString();
            return `/api/inscriptions/export/${format}${qs ? '?' + qs : ''}`;
        },

        /**
         * Charge en parallèle tous les référentiels nécessaires aux sélecteurs de filtres.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const resultats = await Promise.all([
                    fetch(urlSessions),
                    fetch(urlFormations),
                    fetch(urlClients),
                    fetch(urlParticipants),
                ]);
                const [sessionsRes, formationsRes, clientsRes, participantsRes] = resultats;
                if (![sessionsRes, formationsRes, clientsRes, participantsRes].every(res => res.ok)) {
                    throw new Error('Réponse serveur invalide');
                }
                [this.sessions, this.formations, this.clients, this.participants] = await Promise.all(
                    resultats.map(res => res.json())
                );
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement inscriptions :', err);
                this.erreur = 'Impossible de charger les inscriptions.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Construit l'URL de l'API avec les filtres actifs (tous les champs non vides).
         * @returns {string}
         */
        urlFiltree() {
            const params = new URLSearchParams();
            Object.entries(this.filtres).forEach(([cle, valeur]) => {
                if (valeur !== '' && valeur !== null && valeur !== undefined) {
                    params.set(cle, valeur);
                }
            });
            return params.toString() ? `${urlInscriptions}?${params}` : urlInscriptions;
        },

        /**
         * Exécute la requête API et met à jour la liste des inscriptions.
         * Valide préalablement la cohérence des bornes de dates.
         * @param {boolean} gererChargement Affiche/masque l'overlay de chargement.
         * @param {boolean} majHistorique Synchronise l'URL navigateur.
         * @returns {Promise<void>}
         */
        async appliquerFiltres(gererChargement = true, majHistorique = true) {
            // Validation de la cohérence temporelle des bornes de date avant envoi
            if (this.filtres.date_debut_min && this.filtres.date_debut_max && this.filtres.date_debut_min > this.filtres.date_debut_max) {
                this.erreur = 'La date minimale doit être antérieure ou égale à la date maximale.';
                return;
            }
            if (gererChargement) this.chargementEnCours = true;
            this.erreur = null;
            if (majHistorique) {
                this.synchroniserUrlNavigateur(false);
            }
            try {
                const res = await fetch(this.urlFiltree());
                const data = await res.json();
                if (!res.ok) throw new Error(data.erreur || 'Réponse serveur invalide');
                this.inscriptions = data;
            } catch (err) {
                console.error('Erreur filtrage inscriptions :', err);
                this.inscriptions = [];
                this.erreur = err.message || 'Impossible de charger les inscriptions.';
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /** Réinitialise tous les filtres et recharge la liste complète. */
        reinitialiserFiltres() {
            this.filtres = {
                statut: '',
                session_id: '',
                formation_id: '',
                client_id: '',
                participant_id: '',
                date_debut_min: '',
                date_debut_max: '',
            };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        /**
         * Filtre la liste des sessions selon la formation sélectionnée pour le sélecteur en cascade.
         * @returns {Array}
         */
        sessionsFiltreesParFormation() {
            if (!this.filtres.formation_id) return this.sessions;
            return this.sessions.filter(s => String(s.formation?.id) === String(this.filtres.formation_id));
        },

        /**
         * Filtre la liste des participants selon le client sélectionné pour le sélecteur en cascade.
         * @returns {Array}
         */
        participantsFiltresParClient() {
            if (!this.filtres.client_id) return this.participants;
            return this.participants.filter(p => String(p.client?.id) === String(this.filtres.client_id));
        },

        /**
         * Réinitialise le filtre session si la formation change et invalide la session précédente.
         */
        changerFormation() {
            const sessionsDispo = this.sessionsFiltreesParFormation();
            if (!sessionsDispo.some(s => String(s.id) === String(this.filtres.session_id))) {
                this.filtres.session_id = '';
            }
        },

        /**
         * Réinitialise le filtre participant si le client change et invalide le participant précédent.
         */
        changerClient() {
            const participantsDispo = this.participantsFiltresParClient();
            if (!participantsDispo.some(p => String(p.id) === String(this.filtres.participant_id))) {
                this.filtres.participant_id = '';
            }
        },

        /**
         * Indique si au moins un filtre est actif.
         * @returns {boolean}
         */
        aDesFiltresActifs() {
            return Object.values(this.filtres).some(v => v !== '' && v !== null && v !== undefined);
        },

        /**
         * Construit un libellé synthétique pour une option de session dans un sélecteur.
         * @param {object} session Objet session.
         * @returns {string}
         */
        libelleSession(session) {
            return `${session.formation?.titre || 'Formation'} — ${session.date_debut}`;
        },

        /**
         * Renvoie le libellé français du statut d'inscription.
         * @param {string} statut Statut technique.
         * @returns {string}
         */
        libelleStatut(statut) {
            const labels = {
                confirmee: 'Confirmée',
                annulee: 'Annulée',
                liste_attente: "Liste d'attente",
            };
            return labels[statut] || statut;
        },

        /**
         * Renvoie les classes CSS du badge de statut d'inscription.
         * @param {string} statut Statut technique.
         * @returns {string}
         */
        classeStatut(statut) {
            return COULEURS_STATUT_INSCRIPTION[statut] || 'bg-gray-100 text-gray-600';
        },
    };
}

/**
 * @file dashboard.js
 * @description Composant Alpine.js pour le tableau de bord de pilotage de l'organisme.
 * Gère les filtres croisés (Année, Domaine, Client, Formateur), la synchronisation URL
 * (deep linking / popstate), le chargement parallèle des KPIs, des alertes, des sessions
 * à venir et le rendu des graphiques Chart.js (répartition par domaine, évolution temporelle).
 */

// ============================================================
// Variables globales pour les instances Chart.js (singleton)
// Destruction explicite avant tout rechargement pour éviter les fuites mémoire
// ============================================================

/** @type {Chart|null} Instance du graphique en barres "Sessions par domaine" */
let chartDomaineInstance = null;

/** @type {Chart|null} Instance du graphique en courbe "Évolution mensuelle des inscriptions" */
let chartEvolutionInstance = null;

/** @type {string[]} Abréviations françaises des mois pour les axes temporels */
const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

/**
 * Formate un couple (année, numéro de mois) en libellé abrégé lisible pour les axes Chart.js.
 * @param {number} annee Année sur 4 chiffres.
 * @param {number} mois Numéro du mois entre 1 et 12.
 * @returns {string} Ex : "Fév. 2025".
 */
function formaterMoisAnnee(annee, mois) {
    return `${MOIS_ABREGES[mois - 1]} ${annee}`;
}

/**
 * Composant Alpine.js principal du tableau de bord de pilotage.
 * @returns {object} État réactif et méthodes du tableau de bord.
 */
function pageDashboardData() {
    return {
        /** @type {{annee: string, domaine_id: string, client_id: string, formateur_id: string}} Critères de filtre actifs */
        filtres: {
            annee: '',
            domaine_id: '',
            client_id: '',
            formateur_id: '',
        },

        /** @type {object} Métriques globales KPI renvoyées par l'API */
        kpi: {},

        /** @type {{total: number, items: Array}} Alertes opérationnelles (sessions sous-remplies, formateurs sans session…) */
        pointsAttention: { total: 0, items: [] },

        /** @type {Array} Tableau récapitulatif de l'activité par formateur */
        tableFormateurs: [],

        /** @type {Array} 5 prochaines sessions ordonnées chronologiquement */
        sessionsAVenir: [],

        /** @type {Array} Liste des domaines disponibles pour le filtre */
        optionDomaines: [],

        /** @type {Array} Liste des entreprises clientes pour le filtre */
        optionClients: [],

        /** @type {Array} Liste des formateurs pour le filtre */
        optionFormateurs: [],

        /** @type {number[]} Années disponibles dans le sélecteur */
        anneesDisponibles: [2024, 2025, 2026, 2027],

        /** @type {boolean} Indicateur de chargement global */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur éventuel */
        erreur: null,

        /**
         * Génère un message de salutation contextuel selon l'heure locale.
         * @param {string} nom Prénom ou nom de l'utilisateur connecté.
         * @returns {string} Ex : "Bon après-midi Youssef".
         */
        obtenirSalutation(nom) {
            const h = new Date().getHours();
            let prefix = 'Bonjour';
            if (h >= 12 && h < 18) {
                prefix = 'Bon après-midi';
            } else if (h >= 18 || h < 5) {
                prefix = 'Bonsoir';
            }
            return nom ? `${prefix} ${nom}` : prefix;
        },

        /**
         * Renvoie le libellé texte du domaine actuellement filtré.
         * @returns {string}
         */
        libelleDomaine() {
            if (!this.filtres.domaine_id) return 'Tous les domaines';
            const d = this.optionDomaines.find(item => String(item.id) === String(this.filtres.domaine_id));
            return d ? d.nom : `Domaine #${this.filtres.domaine_id}`;
        },

        /**
         * Renvoie le libellé texte du client actuellement filtré.
         * @returns {string}
         */
        libelleClient() {
            if (!this.filtres.client_id) return 'Toutes les entreprises';
            const c = this.optionClients.find(item => String(item.id) === String(this.filtres.client_id));
            return c ? c.nom_entreprise : `Client #${this.filtres.client_id}`;
        },

        /**
         * Renvoie le libellé texte du formateur actuellement filtré.
         * @returns {string}
         */
        libelleFormateur() {
            if (!this.filtres.formateur_id) return 'Tous les formateurs';
            const f = this.optionFormateurs.find(item => String(item.id) === String(this.filtres.formateur_id));
            return f ? f.nom : `Formateur #${this.filtres.formateur_id}`;
        },

        /**
         * Indique si au moins un filtre est actif (pour afficher le bouton "Réinitialiser").
         * @returns {boolean}
         */
        aDesFiltresActifs() {
            return !!(this.filtres.annee || this.filtres.domaine_id || this.filtres.client_id || this.filtres.formateur_id);
        },

        /**
         * Enregistre l'écouteur popstate pour la navigation arrière/avant avec filtres persistés dans l'URL.
         */
        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        /**
         * Lit les paramètres GET de l'URL courante et les injecte dans l'état des filtres.
         */
        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.annee = params.get('annee') || '';
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.client_id = params.get('client_id') || '';
            this.filtres.formateur_id = params.get('formateur_id') || '';
        },

        /**
         * Écrit les filtres actifs dans l'URL via History API (sans rechargement de page).
         * @param {boolean} reinitialiser Si vrai, efface les paramètres d'URL.
         */
        synchroniserUrlNavigateur(reinitialiser = false) {
            if (reinitialiser) {
                if (window.location.search) {
                    window.history.pushState(null, '', window.location.pathname);
                }
                return;
            }
            const params = new URLSearchParams();
            if (this.filtres.annee) params.set('annee', this.filtres.annee);
            if (this.filtres.domaine_id) params.set('domaine_id', this.filtres.domaine_id);
            if (this.filtres.client_id) params.set('client_id', this.filtres.client_id);
            if (this.filtres.formateur_id) params.set('formateur_id', this.filtres.formateur_id);

            const query = params.toString();
            const cible = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            if (window.location.pathname + window.location.search !== cible) {
                window.history.pushState(null, '', cible);
            }
        },

        /**
         * Construit la chaîne de paramètres GET à partir des filtres actifs.
         * @returns {string} Ex : "?annee=2025&domaine_id=1"
         */
        construireQueryString() {
            const params = new URLSearchParams();
            if (this.filtres.annee) params.set('annee', this.filtres.annee);
            if (this.filtres.domaine_id) params.set('domaine_id', this.filtres.domaine_id);
            if (this.filtres.client_id) params.set('client_id', this.filtres.client_id);
            if (this.filtres.formateur_id) params.set('formateur_id', this.filtres.formateur_id);
            const query = params.toString();
            return query ? `?${query}` : '';
        },

        /**
         * Génère l'URL complète pour l'export PDF du rapport de tableau de bord avec les filtres actifs.
         * @returns {string}
         */
        urlExportPdf() {
            return `/api/stats/export/pdf${this.construireQueryString()}`;
        },

        /**
         * Charge les listes de référence (domaines, clients, formateurs) en parallèle.
         * @returns {Promise<void>}
         */
        async chargerOptions() {
            try {
                const [resD, resC, resF] = await Promise.all([
                    fetch(typeof urlDomaines !== 'undefined' ? urlDomaines : '/api/domaines'),
                    fetch(typeof urlClients !== 'undefined' ? urlClients : '/api/clients'),
                    fetch(typeof urlFormateurs !== 'undefined' ? urlFormateurs : '/api/formateurs'),
                ]);
                if (resD.ok) this.optionDomaines = await resD.json();
                if (resC.ok) this.optionClients = await resC.json();
                if (resF.ok) this.optionFormateurs = await resF.json();
            } catch (err) {
                console.error('Erreur chargement options filtres :', err);
            }
        },

        /**
         * Point d'entrée principal appelé par Alpine.js au montage du composant.
         * Charge les options, lit les filtres URL puis déclenche le premier chargement des données.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                await this.chargerOptions();
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement dashboard :', err);
                this.erreur = 'Impossible de charger le tableau de bord.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Déclenche le rechargement de toutes les métriques en appliquant les filtres actifs.
         * Réalise 6 requêtes en parallèle (KPI, domaines, évolution, formateurs, sessions, alertes).
         * @param {boolean} gererChargement Affiche/masque l'overlay de chargement.
         * @param {boolean} majHistorique Synchronise l'URL navigateur.
         * @returns {Promise<void>}
         */
        async appliquerFiltres(gererChargement = true, majHistorique = true) {
            if (gererChargement) this.chargementEnCours = true;
            this.erreur = null;

            if (majHistorique) {
                this.synchroniserUrlNavigateur(false);
            }

            const qs = this.construireQueryString();

            try {
                const [resKpi, resDom, resEvol, resFmt, resSess, resPts] = await Promise.all([
                    fetch(`${urlKpiGlobaux}${qs}`),
                    fetch(`${urlDomaine}${qs}`),
                    fetch(`${urlEvolution}${qs}`),
                    fetch(`${urlFormateur}${qs}`),
                    fetch(`${urlSessions}${qs}`),
                    fetch(`${urlPointsAttention}${qs}`),
                ]);

                if (!resKpi.ok) {
                    const errJson = await resKpi.json().catch(() => ({}));
                    throw new Error(errJson.erreur || 'Erreur lors de la récupération des métriques');
                }

                this.kpi = await resKpi.json();
                const dataDomaine = resDom.ok ? await resDom.json() : [];
                const dataEvolution = resEvol.ok ? await resEvol.json() : [];
                this.tableFormateurs = resFmt.ok ? await resFmt.json() : [];
                const rawSessions = resSess.ok ? await resSess.json() : [];
                this.pointsAttention = resPts.ok ? await resPts.json() : { total: 0, items: [] };

                // Sélection des prochaines sessions : exclure le passé et ordonner chronologiquement (max 5)
                const aujourdHui = new Date();
                aujourdHui.setHours(0, 0, 0, 0);
                this.sessionsAVenir = rawSessions
                    .filter(s => new Date(s.date_debut) >= aujourdHui)
                    .sort((a, b) => new Date(a.date_debut) - new Date(b.date_debut))
                    .slice(0, 5);

                // Rendu des deux graphiques Chart.js
                this.rendreChartDomaine(dataDomaine);
                this.rendreChartEvolution(dataEvolution);

            } catch (err) {
                console.error('Erreur application filtres :', err);
                this.erreur = err.message || 'Impossible de charger les données du tableau de bord.';
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Réinitialise tous les filtres et recharge les données sans paramètre.
         */
        reinitialiserFiltres() {
            this.filtres = { annee: '', domaine_id: '', client_id: '', formateur_id: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        /**
         * Construit et affiche le graphique en barres de la répartition des sessions par domaine.
         * Applique les couleurs de marque propres à chaque domaine d'expertise.
         * @param {Array<{domaine: string, nb_sessions: number}>} data Données de répartition.
         */
        rendreChartDomaine(data) {
            const canvas = document.getElementById('chartDomaine');
            if (!canvas) return;

            // Destruction de l'instance précédente pour éviter les duplicatas Chart.js
            if (chartDomaineInstance) {
                chartDomaineInstance.destroy();
                chartDomaineInstance = null;
            }

            const labels = data.map(d => d.domaine);
            const valeurs = data.map(d => d.nb_sessions);

            // Attribution des couleurs sémantiques par domaine d'expertise
            const couleurs = labels.map(nom => {
                if (!nom) return '#047857';
                if (nom.includes('Cyber')) return '#059669';
                if (nom.includes('Web') || nom.includes('Data')) return '#2563EB';
                if (nom.includes('Agile') || nom.includes('Management')) return '#F26B1F';
                return '#7C3AED';
            });

            chartDomaineInstance = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Sessions',
                        data: valeurs,
                        backgroundColor: couleurs,
                        borderRadius: 8,
                        maxBarThickness: 40,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 650,
                        easing: 'easeOutQuart',
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0F172A',
                            titleFont: { family: 'Inter', size: 12, weight: 'bold' },
                            bodyFont: { family: 'Inter', size: 12 },
                            padding: 10,
                            cornerRadius: 8,
                        }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#F1F5F9' } },
                        x: { grid: { display: false }, ticks: { maxRotation: 0, minRotation: 0, font: { family: 'Inter', size: 11 } } }
                    }
                }
            });
        },

        /**
         * Construit et affiche le graphique en courbe de l'évolution mensuelle des inscriptions.
         * Calcule et affiche également la variation en pourcentage par rapport au mois précédent.
         * @param {Array<{annee: number, mois: number, nb_inscriptions: number}>} data Série temporelle mensuelle.
         */
        rendreChartEvolution(data) {
            const canvas = document.getElementById('chartEvolution');
            if (!canvas) return;

            if (chartEvolutionInstance) {
                chartEvolutionInstance.destroy();
                chartEvolutionInstance = null;
            }

            // Calcul de la tendance mensuelle si au moins deux points de données sont disponibles
            const elTendance = document.getElementById('kpi-participants-tendance');
            if (elTendance) {
                if (data.length >= 2) {
                    const dernier = data[data.length - 1].nb_inscriptions;
                    const prec = data[data.length - 2].nb_inscriptions;
                    if (prec > 0) {
                        const variation = ((dernier - prec) / prec) * 100;
                        const signe = variation >= 0 ? '+' : '';
                        elTendance.textContent = `${signe}${variation.toFixed(0)}% vs mois précédent`;
                        elTendance.className = `text-xs mt-1 font-semibold ${variation >= 0 ? 'text-emerald-700' : 'text-red-600'}`;
                    } else {
                        elTendance.textContent = '';
                    }
                } else {
                    elTendance.textContent = '';
                }
            }

            const labels = data.map(d => formaterMoisAnnee(d.annee, d.mois));
            const valeurs = data.map(d => d.nb_inscriptions);

            chartEvolutionInstance = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Inscriptions',
                        data: valeurs,
                        borderColor: '#047857',
                        backgroundColor: 'rgba(4, 120, 87, 0.08)',
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2.5,
                        pointBackgroundColor: '#047857',
                        pointBorderColor: '#FFFFFF',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#F26B1F',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 750,
                        easing: 'easeOutQuart',
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0F172A',
                            titleFont: { family: 'Inter', size: 12, weight: 'bold' },
                            bodyFont: { family: 'Inter', size: 12 },
                            padding: 10,
                            cornerRadius: 8,
                        }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#F1F5F9' } },
                        x: { grid: { display: false }, ticks: { maxRotation: 0, minRotation: 0, font: { family: 'Inter', size: 11 } } }
                    }
                }
            });
        },
    };
}

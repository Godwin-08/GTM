// ============================================================
// Composant Alpine.js pour le Dashboard de pilotage (PageDashboardData)
// Gère l'état des filtres (Année, Domaine, Client, Formateur),
// la réactivité des KPIs, des graphiques Chart.js, des alertes
// et la synchronisation complète avec l'URL (deep linking / popstate).
// ============================================================

let chartDomaineInstance = null;
let chartEvolutionInstance = null;

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

function formaterMoisAnnee(annee, mois) {
    return `${MOIS_ABREGES[mois - 1]} ${annee}`;
}

function pageDashboardData() {
    return {
        filtres: {
            annee: '',
            domaine_id: '',
            client_id: '',
            formateur_id: '',
        },
        kpi: {},
        pointsAttention: { total: 0, items: [] },
        tableFormateurs: [],
        sessionsAVenir: [],
        optionDomaines: [],
        optionClients: [],
        optionFormateurs: [],
        anneesDisponibles: [2024, 2025, 2026, 2027],
        chargementEnCours: true,
        erreur: null,

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

        libelleDomaine() {
            if (!this.filtres.domaine_id) return 'Tous les domaines';
            const d = this.optionDomaines.find(item => String(item.id) === String(this.filtres.domaine_id));
            return d ? d.nom : `Domaine #${this.filtres.domaine_id}`;
        },

        libelleClient() {
            if (!this.filtres.client_id) return 'Toutes les entreprises';
            const c = this.optionClients.find(item => String(item.id) === String(this.filtres.client_id));
            return c ? c.nom_entreprise : `Client #${this.filtres.client_id}`;
        },

        libelleFormateur() {
            if (!this.filtres.formateur_id) return 'Tous les formateurs';
            const f = this.optionFormateurs.find(item => String(item.id) === String(this.filtres.formateur_id));
            return f ? f.nom : `Formateur #${this.filtres.formateur_id}`;
        },

        aDesFiltresActifs() {
            return !!(this.filtres.annee || this.filtres.domaine_id || this.filtres.client_id || this.filtres.formateur_id);
        },

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.annee = params.get('annee') || '';
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.client_id = params.get('client_id') || '';
            this.filtres.formateur_id = params.get('formateur_id') || '';
        },

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

        construireQueryString() {
            const params = new URLSearchParams();
            if (this.filtres.annee) params.set('annee', this.filtres.annee);
            if (this.filtres.domaine_id) params.set('domaine_id', this.filtres.domaine_id);
            if (this.filtres.client_id) params.set('client_id', this.filtres.client_id);
            if (this.filtres.formateur_id) params.set('formateur_id', this.filtres.formateur_id);
            const query = params.toString();
            return query ? `?${query}` : '';
        },

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

                // Filtrage sessions à venir (futures)
                const aujourdHui = new Date();
                aujourdHui.setHours(0, 0, 0, 0);
                this.sessionsAVenir = rawSessions
                    .filter(s => new Date(s.date_debut) >= aujourdHui)
                    .sort((a, b) => new Date(a.date_debut) - new Date(b.date_debut))
                    .slice(0, 5);

                // Rendu des graphiques
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

        reinitialiserFiltres() {
            this.filtres = { annee: '', domaine_id: '', client_id: '', formateur_id: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        rendreChartDomaine(data) {
            const canvas = document.getElementById('chartDomaine');
            if (!canvas) return;

            if (chartDomaineInstance) {
                chartDomaineInstance.destroy();
                chartDomaineInstance = null;
            }

            const labels = data.map(d => d.domaine);
            const valeurs = data.map(d => d.nb_sessions);

            chartDomaineInstance = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Sessions',
                        data: valeurs,
                        backgroundColor: '#047857',
                        hoverBackgroundColor: '#065F46',
                        borderRadius: 8,
                        maxBarThickness: 36,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#F1F5F9' } },
                        x: { grid: { display: false }, ticks: { maxRotation: 0, minRotation: 0 } }
                    }
                }
            });
        },

        rendreChartEvolution(data) {
            const canvas = document.getElementById('chartEvolution');
            if (!canvas) return;

            if (chartEvolutionInstance) {
                chartEvolutionInstance.destroy();
                chartEvolutionInstance = null;
            }

            // Calcul tendance si données suffisantes
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
                        borderColor: '#7C3AED',
                        backgroundColor: 'rgba(124, 58, 237, 0.08)',
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#7C3AED',
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#F26B1F',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#F1F5F9' } },
                        x: { grid: { display: false }, ticks: { maxRotation: 0, minRotation: 0 } }
                    }
                }
            });
        },
    };
}

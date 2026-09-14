/**
 * @file acp.js
 * @description Contrôleur Alpine.js pour la vue d'analyse factorielle (ACP - Analyse en Composantes Principales).
 * Gère le chargement asynchrone des projections, la construction interactive du scatter plot Chart.js,
 * la qualification statistique de la qualité de représentation (cos²) et des contributions (CTR),
 * ainsi que la mise en évidence visuelle des profils clients atypiques.
 */

// ============================================================
// Page /analytics/acp : Plan factoriel et synthèse métier ACP
// Identité Visuelle : Violet Analytics (#7C3AED) + Touche Orange (#F97316)
// ============================================================

/**
 * Composant de données Alpine.js pour la restitution de l'ACP.
 * @returns {object} État et méthodes réactives d'Alpine.js.
 */
function pageAcpData() {
    return {
        /** @type {object|null} Données statistiques complètes renvoyées par l'API backend (/api/stats/acp) */
        donnees: null,

        /** @type {boolean} Indicateur d'état de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur éventuel */
        erreur: null,

        /** @type {boolean} Bascule d'affichage entre la vue graphique simplifiée et la vue tabulaire détaillée */
        vueStatistique: false,

        /**
         * Charge les résultats factoriels depuis l'API REST et initialise le graphique interactif.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const res = await fetch(urlAcp);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                this.donnees = await res.json();

                // Attendre la mise à jour du DOM pour instancier Chart.js et rafraîchir les icônes Lucide
                this.$nextTick(() => {
                    this.dessinerGraphique();
                    if (window.lucide) {
                        window.lucide.createIcons();
                    }
                });

            } catch (err) {
                console.error('Erreur chargement ACP :', err);
                this.erreur = "Impossible de calculer l'ACP.";
            } finally {
                this.chargementEnCours = false;
            }
        },

        /**
         * Qualifie la qualité de représentation d'un point sur le plan factoriel (cosinus carré cumulé F1+F2).
         * @param {number} cos2Total Somme des cosinus carrés sur les deux premiers axes factoriels (entre 0 et 1).
         * @returns {{pct: string, label: string, badge: string}} Métriques et classes CSS de badge.
         */
        qualifierCos2(cos2Total) {
            const pct = Math.round(cos2Total * 100);
            if (cos2Total >= 0.70) {
                return { pct: `${pct}%`, label: 'Excellente', badge: 'bg-purple-100 text-purple-800 border-purple-200 font-medium' };
            } else if (cos2Total >= 0.50) {
                return { pct: `${pct}%`, label: 'Bonne', badge: 'bg-indigo-100 text-indigo-800 border-indigo-200 font-medium' };
            } else if (cos2Total >= 0.30) {
                return { pct: `${pct}%`, label: 'Moyenne', badge: 'bg-amber-100 text-amber-800 border-amber-200 font-medium' };
            } else {
                return { pct: `${pct}%`, label: 'Faible (Déformé)', badge: 'bg-rose-100 text-rose-700 border-rose-200 font-medium' };
            }
        },

        /**
         * Qualifie l'influence d'un individu ou d'une variable dans la construction d'un axe (Contribution relative CTR).
         * @param {number} ctr Valeur de contribution en pourcentage (0 à 100).
         * @param {number} totalItems Nombre total d'éléments (seuil théorique uniforme = 100 / N).
         * @returns {{label: string, isMajeur: boolean, badge: string}}
         */
        qualifierCtr(ctr, totalItems) {
            const seuilMoyen = totalItems > 0 ? (100 / totalItems) : 10;
            if (ctr >= seuilMoyen * 1.5) {
                return { label: 'Majeure', isMajeur: true, badge: 'bg-purple-100 text-purple-700 font-semibold' };
            } else if (ctr >= seuilMoyen) {
                return { label: 'Moyenne', isMajeur: false, badge: 'bg-slate-100 text-slate-600' };
            } else {
                return { label: 'Faible', isMajeur: false, badge: 'text-slate-400' };
            }
        },

        /**
         * Instancie et configure le nuage de points (Scatter Plot) Chart.js sur les axes F1 et F2.
         */
        dessinerGraphique() {
            const ctx = document.getElementById('chartAcp');
            if (!ctx || !this.donnees || !this.donnees.clients) return;

            const distinctNom = this.donnees.interpretation?.client_distinct?.nom || null;

            // Attribution dynamique des couleurs en fonction de la qualité cos² et de la détection d'atypie
            const bgColors = this.donnees.clients.map(c => {
                // Touche orange pour le profil singulier atypique identifié par l'algorithme
                if (distinctNom && c.nom === distinctNom) {
                    return '#EA580C'; // Orange chaud accent
                }
                const cos2 = c.cos2_f1 + c.cos2_f2;
                if (cos2 >= 0.70) return '#6D28D9'; // Violet profond haute fidélité
                if (cos2 >= 0.50) return '#7C3AED'; // Violet Analytics
                return '#94A3B8'; // Gris ardoise (faible qualité)
            });

            // Dimensionnement des rayons de points selon la représentativité
            const radius = this.donnees.clients.map(c => {
                if (distinctNom && c.nom === distinctNom) return 9; // Point élargi pour le profil singulier
                const cos2 = c.cos2_f1 + c.cos2_f2;
                return cos2 >= 0.50 ? 7 : 4.5;
            });

            new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Clients',
                        data: this.donnees.clients.map(c => ({ x: c.f1, y: c.f2 })),
                        backgroundColor: bgColors,
                        borderColor: bgColors,
                        pointRadius: radius,
                        pointHoverRadius: 10,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#0F172A',
                            titleColor: '#F8FAFC',
                            bodyColor: '#E2E8F0',
                            padding: 12,
                            cornerRadius: 8,
                            callbacks: {
                                label: (contexte) => {
                                    const client = this.donnees.clients[contexte.dataIndex];
                                    const cos2Total = client.cos2_f1 + client.cos2_f2;
                                    const qualite = this.qualifierCos2(cos2Total);
                                    const isDistinct = distinctNom && client.nom === distinctNom;
                                    const tags = isDistinct ? ' [ Profil Atypique ]' : '';
                                    return [
                                        ` Entreprise : ${client.nom}${tags}`,
                                        ` Coordonnées : F1=${client.f1.toFixed(2)}, F2=${client.f2.toFixed(2)}`,
                                        ` Qualité de la vue : ${qualite.pct} (${qualite.label})`,
                                        ` Poids sur la tendance F1 : ${client.ctr_f1.toFixed(1)}%`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: `Axe principal F1 — Tendance dominante (${this.donnees.variance_expliquee.par_axe[0] || 0}% de variance)`,
                                font: { weight: 'bold', size: 12 },
                                color: '#4C1D95'
                            },
                            grid: { color: '#F1F5F9' },
                        },
                        y: {
                            title: {
                                display: true,
                                text: `Axe secondaire F2 — Nuance de profil (${this.donnees.variance_expliquee.par_axe[1] || 0}% de variance)`,
                                font: { weight: 'bold', size: 12 },
                                color: '#4C1D95'
                            },
                            grid: { color: '#F1F5F9' },
                        }
                    }
                }
            });
        },
    };
}

// ============================================================
// Page /analytics/acp : Plan factoriel et synthèse métier ACP
// Identité Visuelle : Violet Analytics (#7C3AED) + Touche Orange (#F97316)
// ============================================================

function pageAcpData() {
    return {
        donnees: null,
        chargementEnCours: true,
        erreur: null,
        vueStatistique: false,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const res = await fetch(urlAcp);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                this.donnees = await res.json();

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

        // Helper pour qualifier le cos2 (Qualité de représentation)
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

        // Helper pour qualifier la contribution (CTR)
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

        dessinerGraphique() {
            const ctx = document.getElementById('chartAcp');
            if (!ctx || !this.donnees || !this.donnees.clients) return;

            const distinctNom = this.donnees.interpretation?.client_distinct?.nom || null;

            const bgColors = this.donnees.clients.map(c => {
                // Touche orange pour le profil singulier atypique détecté
                if (distinctNom && c.nom === distinctNom) {
                    return '#EA580C'; // Orange chaud accent
                }
                const cos2 = c.cos2_f1 + c.cos2_f2;
                if (cos2 >= 0.70) return '#6D28D9'; // Deep violet
                if (cos2 >= 0.50) return '#7C3AED'; // Violet Analytics
                return '#94A3B8'; // Slate 400
            });

            const radius = this.donnees.clients.map(c => {
                if (distinctNom && c.nom === distinctNom) return 9; // Légèrement mis en avant
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

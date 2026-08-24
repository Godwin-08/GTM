// ============================================================
// Page /analytics/acp : Plan factoriel et synthèse métier ACP
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

        dessinerGraphique() {
            const ctx = document.getElementById('chartAcp');
            if (!ctx || !this.donnees) return;

            const bgColors = this.donnees.clients.map(c =>
                (c.cos2_f1 + c.cos2_f2) >= 0.5 ? '#F26B1F' : '#9CA3AF'
            );
            const radius = this.donnees.clients.map(c =>
                (c.cos2_f1 + c.cos2_f2) >= 0.5 ? 7 : 5
            );

            new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Clients',
                        data: this.donnees.clients.map(c => ({ x: c.f1, y: c.f2 })),
                        backgroundColor: bgColors,
                        pointRadius: radius,
                        pointHoverRadius: 9,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (contexte) => {
                                    const client = this.donnees.clients[contexte.dataIndex];
                                    const cos2Total = (client.cos2_f1 + client.cos2_f2).toFixed(2);
                                    const qualiteStr = (client.cos2_f1 + client.cos2_f2) >= 0.5 ? 'Fiable' : 'Insuffisante';
                                    return `${client.nom} | cos²(F1+F2): ${cos2Total} (${qualiteStr})`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: `Axe principal F1 (${this.donnees.variance_expliquee.par_axe[0]}% de variance)`
                            },
                            grid: { color: '#F3F4F6' },
                        },
                        y: {
                            title: {
                                display: true,
                                text: `Axe secondaire F2 (${this.donnees.variance_expliquee.par_axe[1]}% de variance)`
                            },
                            grid: { color: '#F3F4F6' },
                        }
                    }
                }
            });
        },
    };
}

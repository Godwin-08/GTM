// ============================================================
// Ce script charge les vraies données de GTM et remplit
// le dashboard : KPI, graphiques, tableau formateurs.
// Toutes les URLs viennent de variables déclarées dans
// dashboard.html (générées par Jinja2 via url_for).
// ============================================================

function afficherErreur(elementId, message = "Erreur de chargement") {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.add('text-red-500', 'text-sm', 'font-normal');
    }
}

// Table de correspondance mois -> abréviation française
const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

// Transforme {annee: 2026, mois: 1} en "Jan. 2026"
function formaterMoisAnnee(annee, mois) {
    // mois arrive en 1-12, le tableau est indexé 0-11 -> on soustrait 1
    return `${MOIS_ABREGES[mois - 1]} ${annee}`;
}

// Calcule la variation en % entre le dernier mois et le mois précédent,
// à partir des données déjà récupérées pour le graphique d'évolution.
function afficherTendanceParticipants(data) {
    // data est le tableau brut de evolution-inscriptions, trié chronologiquement
    if (data.length < 2) return; // pas assez de données pour comparer

    const dernierMois = data[data.length - 1].nb_inscriptions;
    const moisPrecedent = data[data.length - 2].nb_inscriptions;

    const el = document.getElementById('kpi-participants-tendance');
    if (!el) return;

    // Évite une division par zéro si le mois précédent était à 0 inscription
    if (moisPrecedent === 0) {
        el.textContent = '';
        return;
    }

    const variation = ((dernierMois - moisPrecedent) / moisPrecedent) * 100;
    const signe = variation >= 0 ? '+' : '';
    const couleur = variation >= 0 ? 'text-success' : 'text-danger';

    el.textContent = `${signe}${variation.toFixed(0)}% vs mois précédent`;
    el.classList.add(couleur);
}

// --- 1. KPI : Sessions + Taux de remplissage ---
async function chargerKpiRemplissage() {
    try {
        const res = await fetch(urlRemplissage);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const data = await res.json();

        document.getElementById('kpi-sessions').textContent = data.nb_sessions;

        const tauxPourcent = (data.taux_moyen * 100).toFixed(1);
        document.getElementById('kpi-remplissage').textContent = tauxPourcent + '%';

    } catch (err) {
        console.error('Erreur chargement remplissage :', err);
        afficherErreur('kpi-sessions');
        afficherErreur('kpi-remplissage');
    }
}

// --- 2. KPI : Clients actifs + Participants ---
// Les deux se calculent à partir de la même route activite-client,
// donc on ne fait qu'un seul fetch pour les deux.
async function chargerKpiClients() {
    try {
        const res = await fetch(urlClient);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const data = await res.json(); // [{client, nb_inscriptions_confirmees, nb_participants_actifs}, ...]

        // Clients actifs = ceux qui ont au moins une inscription confirmée
        const clientsActifs = data.filter(c => c.nb_inscriptions_confirmees > 0).length;
        document.getElementById('kpi-clients').textContent = clientsActifs;

        // Participants = somme des participants actifs de chaque client
        const totalParticipants = data.reduce((total, c) => total + c.nb_participants_actifs, 0);
        document.getElementById('kpi-participants').textContent = totalParticipants;

    } catch (err) {
        console.error('Erreur chargement clients :', err);
        afficherErreur('kpi-clients');
        afficherErreur('kpi-participants');
    }
}

// --- 3. Graphique : sessions par domaine ---
async function chargerChartDomaine() {
    try {
        const res = await fetch(urlDomaine);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const data = await res.json();

        const labels = data.map(d => d.domaine);
        const valeurs = data.map(d => d.nb_sessions);

        new Chart(document.getElementById('chartDomaine'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sessions',
                    data: valeurs,
                    backgroundColor: '#F26B1F',
                    borderRadius: 4
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#F3F4F6' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });

    } catch (err) {
        console.error('Erreur chargement domaine :', err);
        const canvas = document.getElementById('chartDomaine');
        canvas.insertAdjacentHTML('afterend',
            '<p class="text-sm text-red-500">Impossible de charger ce graphique.</p>');
    }
}

// --- 4. Graphique : évolution des inscriptions ---
async function chargerChartEvolution() {
    try {
        const res = await fetch(urlEvolution);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const data = await res.json();

        // Calcule et affiche la tendance sur la carte Participants
        afficherTendanceParticipants(data);

        const labels = data.map(d => formaterMoisAnnee(d.annee, d.mois));
        const valeurs = data.map(d => d.nb_inscriptions);

        new Chart(document.getElementById('chartEvolution'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Inscriptions',
                    data: valeurs,
                    borderColor: '#F26B1F',
                    backgroundColor: 'rgba(242, 107, 31, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: '#F3F4F6' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });

    } catch (err) {
        console.error('Erreur chargement évolution :', err);
        const canvas = document.getElementById('chartEvolution');
        canvas.insertAdjacentHTML('afterend',
            '<p class="text-sm text-red-500">Impossible de charger ce graphique.</p>');
    }
}

// --- 5. Tableau : performance des formateurs ---
async function chargerTableFormateurs() {
    const tbody = document.getElementById('tableFormateurs');

    tbody.innerHTML = `
        <tr><td colspan="3" class="px-5 py-4 text-center text-gray-400 text-sm">Chargement...</td></tr>
    `;

    try {
        const res = await fetch(urlFormateur);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const data = await res.json();

        if (data.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="3" class="px-5 py-4 text-center text-gray-400 text-sm">Aucune donnée disponible</td></tr>
            `;
            return;
        }

        tbody.innerHTML = data.map(f => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-5 py-3">${f.formateur}</td>
                <td class="px-5 py-3">${f.nb_sessions}</td>
                <td class="px-5 py-3">${(f.taux_remplissage_moyen * 100).toFixed(0)}%</td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Erreur chargement formateurs :', err);
        tbody.innerHTML = `
            <tr><td colspan="3" class="px-5 py-4 text-center text-red-500 text-sm">Impossible de charger les données.</td></tr>
        `;
    }
}

// --- 6. Sessions à venir ---
async function chargerSessionsAVenir() {
    const conteneur = document.getElementById('listeSessionsAVenir');
    conteneur.innerHTML = `<p class="px-5 py-4 text-sm text-gray-400 text-center">Chargement...</p>`;

    try {
        const res = await fetch(urlSessions);
        if (!res.ok) throw new Error('Réponse serveur invalide');
        const sessions = await res.json();

        // On compare avec la date du jour pour ne garder que les sessions futures.
        // On met l'heure à minuit pour comparer uniquement les dates, sans les heures.
        const aujourdHui = new Date();
        aujourdHui.setHours(0, 0, 0, 0);

        const sessionsAVenir = sessions
            .filter(s => new Date(s.date_debut) >= aujourdHui)
            .sort((a, b) => new Date(a.date_debut) - new Date(b.date_debut))
            .slice(0, 5);

        if (sessionsAVenir.length === 0) {
            conteneur.innerHTML = `<p class="px-5 py-4 text-sm text-gray-400 text-center">Aucune session à venir</p>`;
            return;
        }

        conteneur.innerHTML = sessionsAVenir.map(s => {
            // On détermine la couleur du badge selon le taux de remplissage.
            // Seuils choisis arbitrairement pour l'instant : à ajuster plus tard
            // une fois qu'on aura vu tourner davantage de vraies données.
            let badgeCouleur, badgeTexte;
            if (s.est_complete) {
                badgeCouleur = 'bg-gray-100 text-gray-600';
                badgeTexte = 'Complète';
            } else if (s.taux_remplissage >= 0.7) {
                badgeCouleur = 'bg-success/10 text-success';
                badgeTexte = 'Bon remplissage';
            } else if (s.taux_remplissage >= 0.4) {
                badgeCouleur = 'bg-warning/10 text-warning';
                badgeTexte = 'À surveiller';
            } else {
                badgeCouleur = 'bg-danger/10 text-danger';
                badgeTexte = 'Sous-remplie';
            }

            // Formatage simple de la date en français (jour/mois abrégé)
            const date = new Date(s.date_debut);
            const jour = date.getDate();
            const mois = MOIS_ABREGES[date.getMonth()];

            return `
                <div class="flex items-center justify-between px-5 py-3">
                    <div class="min-w-0">
                        <p class="text-sm font-medium text-gray-900 truncate">${s.formation.titre}</p>
                        <p class="text-xs text-gray-500">
                            ${jour} ${mois} · ${s.formateur.nom} · ${s.lieu}
                        </p>
                    </div>
                    <div class="flex items-center gap-3 flex-shrink-0 ml-4">
                        <span class="text-xs text-gray-500">${s.nb_inscrits_confirmes}/${s.capacite_max}</span>
                        <span class="text-xs font-medium px-2 py-1 rounded-full ${badgeCouleur}">
                            ${badgeTexte}
                        </span>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Erreur chargement sessions à venir :', err);
        conteneur.innerHTML = `<p class="px-5 py-4 text-sm text-red-500 text-center">Impossible de charger les sessions.</p>`;
    }
}

// ============================================================
// Lancement de tous les chargements en parallèle.
// Chaque fonction gère son propre état d'erreur indépendamment.
// ============================================================
chargerKpiRemplissage();
chargerKpiClients();
chargerChartDomaine();
chargerChartEvolution();
chargerTableFormateurs();
chargerSessionsAVenir();

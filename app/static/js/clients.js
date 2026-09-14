/**
 * @file clients.js
 * @description Composant Alpine.js pour la liste des entreprises clientes.
 * Gère la recherche multicritère (nom, secteur, statut d'activité), le tri côté client,
 * la synchronisation URL, les modales de création et d'édition, et l'exportation CSV/XLSX.
 */

/** @type {Object<string, string>} Correspondance statut d'activité → classes CSS Tailwind */
const COULEURS_STATUT_ACTIVITE = {
    actif: 'bg-success/10 text-success',
    inactif: 'bg-warning/10 text-warning',
    aucune: 'bg-gray-100 text-gray-600',
};

/**
 * Composant Alpine.js pour la page liste des clients (/clients).
 * @returns {object} État réactif et méthodes de la page.
 */
function pageClientsData() {
    return {
        /** @type {Array} Clients chargés depuis l'API */
        clients: [],

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur de chargement */
        erreur: null,

        /** @type {{q: string, secteur: string, statut_activite: string, tri: string}} Critères de filtrage actifs */
        filtres: {
            q: '',
            secteur: '',
            statut_activite: '',
            tri: '',
        },

        // --- État de la modale de création ---
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom_entreprise: '', secteur: '', contact_email: '' },

        // --- État de la modale d'édition ---
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom_entreprise: '', secteur: '', contact_email: '' },

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
         * Lit les paramètres GET de l'URL courante et hydrate l'état des filtres.
         */
        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.q = params.get('q') || '';
            this.filtres.secteur = params.get('secteur') || '';
            this.filtres.statut_activite = params.get('statut_activite') || '';
            this.filtres.tri = params.get('tri') || '';
        },

        /**
         * Écrit les filtres actifs dans l'URL du navigateur via History API sans rechargement.
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
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.secteur && this.filtres.secteur.trim()) {
                params.set('secteur', this.filtres.secteur.trim());
            }
            if (this.filtres.statut_activite) {
                params.set('statut_activite', this.filtres.statut_activite);
            }
            if (this.filtres.tri) {
                params.set('tri', this.filtres.tri);
            }
            const query = params.toString();
            const cible = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            if (window.location.pathname + window.location.search !== cible) {
                window.history.pushState(null, '', cible);
            }
        },

        /**
         * Construit l'URL de l'API avec les filtres actifs pour la requête fetch.
         * @returns {string} URL complète avec paramètres GET.
         */
        construireUrlFiltree() {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.secteur && this.filtres.secteur.trim()) {
                params.set('secteur', this.filtres.secteur.trim());
            }
            if (this.filtres.statut_activite) {
                params.set('statut_activite', this.filtres.statut_activite);
            }
            const query = params.toString();
            return query ? `${urlClients}?${query}` : urlClients;
        },

        /**
         * Construit l'URL d'export (CSV ou XLSX) avec les filtres actifs.
         * @param {'csv'|'xlsx'} format Format souhaité.
         * @returns {string}
         */
        urlExport(format = 'csv') {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) params.set('q', this.filtres.q.trim());
            if (this.filtres.secteur && this.filtres.secteur.trim()) params.set('secteur', this.filtres.secteur.trim());
            if (this.filtres.statut_activite) params.set('statut_activite', this.filtres.statut_activite);
            const qs = params.toString();
            return `/api/clients/export/${format}${qs ? '?' + qs : ''}`;
        },

        /**
         * Initialisation : lit les filtres URL puis charge les données.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement clients :', err);
                this.erreur = 'Impossible de charger les clients.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Exécute la requête API avec les filtres actifs et met à jour la liste clients.
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
            try {
                const res = await fetch(this.construireUrlFiltree());
                const data = await res.json();
                if (!res.ok) throw new Error(data.erreur || 'Réponse serveur invalide');
                this.clients = data;
            } catch (err) {
                console.error('Erreur filtrage clients :', err);
                this.erreur = err.message || 'Impossible de charger les clients.';
                this.clients = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Réinitialise tous les filtres et recharge la liste sans paramètre.
         */
        reinitialiserFiltres() {
            this.filtres = { q: '', secteur: '', statut_activite: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        /**
         * Applique le tri client-side sur la liste déjà chargée.
         * @returns {Array} Liste de clients triée.
         */
        clientsFiltres() {
            const copie = [...this.clients];
            const t = this.filtres.tri;
            if (t === 'nom_desc') {
                return copie.sort((a, b) => (b.nom_entreprise || '').localeCompare(a.nom_entreprise || '', 'fr'));
            }
            if (t === 'secteur_asc') {
                return copie.sort((a, b) => (a.secteur || '').localeCompare(b.secteur || '', 'fr'));
            }
            if (t === 'statut_asc') {
                const ordre = { actif: 0, inactif: 1, aucune: 2 };
                return copie.sort((a, b) => (ordre[a.statut_activite] ?? 3) - (ordre[b.statut_activite] ?? 3));
            }
            // Tri par défaut : nom A → Z
            return copie.sort((a, b) => (a.nom_entreprise || '').localeCompare(b.nom_entreprise || '', 'fr'));
        },

        /**
         * Renvoie les classes CSS du badge selon le statut d'activité du client.
         * @param {string} statut 'actif' | 'inactif' | 'aucune'.
         * @returns {string}
         */
        classeStatut(statut) {
            return COULEURS_STATUT_ACTIVITE[statut] || 'bg-gray-100 text-gray-600';
        },

        /**
         * Ouvre la modale de création et réinitialise le formulaire.
         */
        ouvrirModaleCreation() {
            this.formulaire = { nom_entreprise: '', secteur: '', contact_email: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        /**
         * Ferme la modale de création si aucun envoi n'est en cours.
         */
        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

        /**
         * Soumet le formulaire de création d'un nouveau client via POST.
         * En cas de succès, ajoute le client à la liste locale sans rechargement complet.
         * @returns {Promise<void>}
         */
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlClients, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom_entreprise: this.formulaire.nom_entreprise,
                        secteur: this.formulaire.secteur || null,
                        contact_email: this.formulaire.contact_email || null,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.clients.push({ ...data, nb_participants: data.nb_participants ?? 0 });
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Client créé avec succès.');
            } catch (err) {
                console.error('Erreur création client :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
            }
        },

        /**
         * Ouvre la modale d'édition pré-remplie avec les données du client sélectionné.
         * @param {object} client Objet client provenant de la liste.
         */
        ouvrirModaleEdition(client) {
            this.edition = {
                id: client.id,
                nom_entreprise: client.nom_entreprise,
                secteur: client.secteur || '',
                contact_email: client.contact_email || '',
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        /**
         * Ferme la modale d'édition si aucun enregistrement n'est en cours.
         */
        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

        /**
         * Soumet les modifications du client via PUT et met à jour l'entrée dans la liste locale.
         * @returns {Promise<void>}
         */
        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;

            try {
                const res = await fetch(`${urlClients}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom_entreprise: this.edition.nom_entreprise,
                        secteur: this.edition.secteur || null,
                        contact_email: this.edition.contact_email || null,
                    }),
                });

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Ce nom d\'entreprise est peut-être déjà utilisé, ou une erreur serveur est survenue.' };
                }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                // Mise à jour optimiste dans la liste locale
                const index = this.clients.findIndex(c => c.id === this.edition.id);
                if (index !== -1) this.clients[index] = { ...data, nb_participants: this.clients[index].nb_participants ?? 0 };
                this.modaleEditionOuverte = false;
            } catch (err) {
                console.error('Erreur modification client :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },
    };
}

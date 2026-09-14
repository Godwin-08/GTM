/**
 * @file formateurs.js
 * @description Composant Alpine.js pour la page liste des formateurs (/formateurs).
 * Gère la recherche multicritère (nom/email, domaine, type interne/externe), le tri côté client,
 * la synchronisation URL (deep linking), les modales de création et d'édition.
 */

/** @type {Object<string, string>} Correspondance domaine → classes CSS Tailwind pour les badges */
const COULEURS_DOMAINE = {
    'Web & Data': 'bg-blue-50 text-blue-700 border border-blue-200/80',
    'Management Agile': 'bg-amber-50 text-amber-800 border border-amber-200/80',
    'Cybersécurité': 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
};

/**
 * Composant Alpine.js pour la page liste des formateurs.
 * @returns {object} État réactif et méthodes de la page.
 */
function pageFormateursData() {
    return {
        /** @type {Array} Formateurs chargés depuis l'API */
        formateurs: [],

        /** @type {Array} Domaines disponibles pour le sélecteur de filtre */
        domaines: [],

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur de chargement */
        erreur: null,

        /** @type {{q: string, domaine_id: string, type: string, tri: string}} Critères de filtrage actifs */
        filtres: {
            q: '',
            domaine_id: '',
            type: '',        // 'interne' | 'externe' | ''
            tri: '',
        },

        // --- État de la modale de création ---
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' },

        // --- État de la modale d'édition ---
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, nom: '', domaine_id: '', email: '', telephone: '', a_un_compte: false },

        /**
         * Enregistre l'écouteur popstate pour la navigation navigateur.
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
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.type = params.get('type') || '';
            this.filtres.tri = params.get('tri') || '';
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
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.domaine_id) {
                params.set('domaine_id', this.filtres.domaine_id);
            }
            if (this.filtres.type) {
                params.set('type', this.filtres.type);
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
         * Construit l'URL de l'API avec les filtres actifs (q, domaine, type).
         * @returns {string}
         */
        construireUrlFiltree() {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) {
                params.set('q', this.filtres.q.trim());
            }
            if (this.filtres.domaine_id) {
                params.set('domaine_id', this.filtres.domaine_id);
            }
            if (this.filtres.type) {
                params.set('type', this.filtres.type);
            }
            const query = params.toString();
            return query ? `${urlFormateurs}?${query}` : urlFormateurs;
        },

        /**
         * Initialisation : charge les domaines, puis les formateurs avec les filtres URL.
         * @returns {Promise<void>}
         */
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const domainesRes = await fetch(urlDomaines);
                if (domainesRes.ok) {
                    this.domaines = await domainesRes.json();
                }
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement formateurs :', err);
                this.erreur = 'Impossible de charger les formateurs.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Exécute la requête API et met à jour la liste des formateurs.
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
                this.formateurs = data;
            } catch (err) {
                console.error('Erreur filtrage formateurs :', err);
                this.erreur = err.message || 'Impossible de charger les formateurs.';
                this.formateurs = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /** Réinitialise tous les filtres et recharge la liste complète. */
        reinitialiserFiltres() {
            this.filtres = { q: '', domaine_id: '', type: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        /**
         * Applique le tri client-side sur la liste des formateurs déjà chargée.
         * @returns {Array} Formateurs triés.
         */
        formateursFiltres() {
            const copie = [...this.formateurs];
            const t = this.filtres.tri;
            if (t === 'nom_desc') return copie.sort((a, b) => b.nom.localeCompare(a.nom));
            if (t === 'domaine_asc') return copie.sort((a, b) => (a.domaine?.nom || '').localeCompare(b.domaine?.nom || ''));
            // Par défaut : nom A → Z
            return copie.sort((a, b) => a.nom.localeCompare(b.nom));
        },

        /** @param {object} formateur @returns {string} Nom du domaine d'expertise. */
        nomDomaine(formateur) { return formateur.domaine?.nom || ''; },

        /**
         * Renvoie les classes CSS du badge de domaine.
         * @param {string} nomDomaine Nom du domaine.
         * @returns {string}
         */
        couleurDomaine(nomDomaine) {
            return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600';
        },

        /** Ouvre la modale de création et réinitialise le formulaire. */
        ouvrirModaleCreation() {
            this.formulaire = { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        /** Ferme la modale de création si aucune requête n'est en cours. */
        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

        /**
         * Soumet la création d'un nouveau formateur via POST.
         * L'identifiant utilisateur est optionnel (formateur interne uniquement).
         * @returns {Promise<void>}
         */
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlFormateurs, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.formulaire.nom,
                        domaine_id: this.formulaire.domaine_id,
                        email: this.formulaire.email || null,
                        telephone: this.formulaire.telephone || null,
                        // Rattachement optionnel à un compte utilisateur (formateur interne)
                        ...(this.formulaire.utilisateur_id ? { utilisateur_id: this.formulaire.utilisateur_id } : {}),
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formateur créé avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur création formateur :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
            }
        },

        /**
         * Ouvre la modale d'édition pré-remplie avec les données du formateur.
         * @param {object} formateur Objet formateur de la liste.
         */
        ouvrirModaleEdition(formateur) {
            this.edition = {
                id: formateur.id,
                nom: formateur.nom,
                domaine_id: formateur.domaine?.id ?? '',
                email: formateur.email || '',
                telephone: formateur.telephone || '',
                a_un_compte: formateur.a_un_compte,
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        /** Ferme la modale d'édition si aucune requête n'est en cours. */
        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

        /**
         * Soumet les modifications du formateur via PUT.
         * @returns {Promise<void>}
         */
        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlFormateurs}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.edition.nom,
                        domaine_id: this.edition.domaine_id,
                        email: this.edition.email || null,
                        telephone: this.edition.telephone || null,
                    }),
                });

                let data;
                try { data = await res.json(); } catch { data = { erreur: 'Erreur inattendue du serveur.' }; }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurEdition);
                    return;
                }

                this.modaleEditionOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formateur modifié avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur modification formateur :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },
    };
}

/**
 * @file formations.js
 * @description Composant Alpine.js pour la page liste des formations du catalogue (/formations).
 * Gère la recherche multicritère (mot-clé, domaine), le tri côté client, la synchronisation URL,
 * les modales de création, d'édition et de suppression (avec contrôle d'intégrité relationnelle côté serveur),
 * ainsi que les helpers de mise en forme visuelle des badges de domaine.
 */

/** @type {Object<string, string>} Correspondance nom de domaine → classes CSS Tailwind pour les badges */
const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

/**
 * Composant Alpine.js pour la page liste des formations.
 * @returns {object} État réactif et méthodes de la page.
 */
function pageFormationsData() {
    return {
        /** @type {Array} Formations chargées depuis l'API */
        formations: [],
        modeSelection: false,
        selectionnees: [],

        /** @type {Array} Domaines disponibles pour le sélecteur de filtre */
        domaines: [],

        /** @type {boolean} Indicateur de chargement réseau */
        chargementEnCours: true,

        /** @type {string|null} Message d'erreur de chargement */
        erreur: null,

        /** @type {{q: string, domaine_id: string, tri: string}} Critères de filtrage actifs */
        filtres: {
            q: '',
            domaine_id: '',
            tri: '',
        },

        // --- État de la modale de création ---
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { titre: '', domaine_id: '', duree_jours: 3, description: '' },

        // --- État de la modale d'édition ---
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, titre: '', domaine_id: '', duree_jours: 3, description: '' },

        // --- État de la modale de suppression ---
        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        /**
         * Enregistre les réactivités et l'écouteur popstate pour la navigation navigateur.
         */
        init() {
            this.$watch('formations', () => {
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
            this.filtres.q = params.get('q') || '';
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.tri = params.get('tri') || '';
        },

        /**
         * Écrit les filtres actifs dans l'URL du navigateur via History API.
         * @param {boolean} reinitialiser Si vrai, efface tous les paramètres d'URL.
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
         * Construit l'URL de l'API avec les filtres actifs (sans le tri, géré côté client).
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
            const query = params.toString();
            return query ? `${urlFormations}?${query}` : urlFormations;
        },

        /**
         * Construit l'URL d'export (CSV ou XLSX) avec les filtres actifs.
         * @param {'csv'|'xlsx'} format Format souhaité.
         * @returns {string}
         */
        urlExport(format = 'csv') {
            const params = new URLSearchParams();
            if (this.filtres.q && this.filtres.q.trim()) params.set('q', this.filtres.q.trim());
            if (this.filtres.domaine_id) params.set('domaine_id', this.filtres.domaine_id);
            const qs = params.toString();
            return `/api/formations/export/${format}${qs ? '?' + qs : ''}`;
        },

        /**
         * Initialisation : charge les domaines et les formations avec les filtres URL.
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
                console.error('Erreur chargement formations :', err);
                this.erreur = 'Impossible de charger les formations.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Exécute la requête API et met à jour la liste des formations.
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
                this.formations = data;
            } catch (err) {
                console.error('Erreur filtrage formations :', err);
                this.erreur = err.message || 'Impossible de charger les formations.';
                this.formations = [];
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        /**
         * Réinitialise tous les filtres et recharge la liste complète.
         */
        reinitialiserFiltres() {
            this.filtres = { q: '', domaine_id: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        /**
         * Applique le tri client-side sur les formations déjà chargées.
         * @returns {Array} Formations triées selon le critère actif.
         */
        formationsFiltrees() {
            const copie = [...this.formations];
            const t = this.filtres.tri;
            if (t === 'titre_desc') return copie.sort((a, b) => b.titre.localeCompare(a.titre));
            if (t === 'duree_desc') return copie.sort((a, b) => b.duree_jours - a.duree_jours);
            if (t === 'duree_asc') return copie.sort((a, b) => a.duree_jours - b.duree_jours);
            if (t === 'domaine_asc') return copie.sort((a, b) => (a.domaine?.nom || '').localeCompare(b.domaine?.nom || ''));
            // Par défaut : titre A → Z
            return copie.sort((a, b) => a.titre.localeCompare(b.titre));
        },

        /** @param {object} formation Instance de formation. @returns {string} Nom du domaine. */
        nomDomaine(formation) { return formation.domaine?.nom || ''; },

        /**
         * Renvoie les classes CSS du gradient de la vignette selon le domaine.
         * @param {string} domaineNom Nom du domaine.
         * @returns {string} Classes de gradient Tailwind.
         */
        domaineGradient(domaineNom) {
            if (!domaineNom) return 'from-slate-400 to-slate-600';
            if (domaineNom.includes('Cyber')) return 'from-emerald-500 to-teal-600';
            if (domaineNom.includes('Web') || domaineNom.includes('Data')) return 'from-blue-500 to-indigo-600';
            if (domaineNom.includes('Agile') || domaineNom.includes('Management')) return 'from-orange-500 to-amber-500';
            return 'from-violet-500 to-purple-600';
        },

        /**
         * Renvoie les classes CSS du badge de domaine.
         * @param {string} domaineNom Nom du domaine.
         * @returns {string}
         */
        domaineBadgeClass(domaineNom) {
            if (!domaineNom) return 'bg-slate-100 text-slate-700 border-slate-200';
            if (domaineNom.includes('Cyber')) return 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
            if (domaineNom.includes('Web') || domaineNom.includes('Data')) return 'bg-blue-50 text-blue-700 border-blue-200/80';
            if (domaineNom.includes('Agile') || domaineNom.includes('Management')) return 'bg-amber-50 text-amber-800 border-amber-200/80';
            return 'bg-purple-50 text-purple-700 border-purple-200/80';
        },

        /**
         * Renvoie l'identifiant d'icône Lucide représentant le domaine.
         * @param {string} domaineNom Nom du domaine.
         * @returns {string}
         */
        domaineIcon(domaineNom) {
            if (!domaineNom) return 'book-open';
            if (domaineNom.includes('Cyber')) return 'shield-check';
            if (domaineNom.includes('Web') || domaineNom.includes('Data')) return 'code-2';
            if (domaineNom.includes('Agile') || domaineNom.includes('Management')) return 'zap';
            return 'graduation-cap';
        },

        /**
         * Renvoie les classes CSS du fond de l'icône de domaine.
         * @param {string} domaineNom Nom du domaine.
         * @returns {string}
         */
        domaineIconBg(domaineNom) {
            if (!domaineNom) return 'bg-slate-100 text-slate-600 border-slate-200';
            if (domaineNom.includes('Cyber')) return 'bg-emerald-50 text-emerald-600 border-emerald-100';
            if (domaineNom.includes('Web') || domaineNom.includes('Data')) return 'bg-blue-50 text-blue-600 border-blue-100';
            if (domaineNom.includes('Agile') || domaineNom.includes('Management')) return 'bg-amber-50 text-amber-600 border-amber-100';
            return 'bg-purple-50 text-purple-600 border-purple-100';
        },

        /** Alias de domaineBadgeClass utilisé dans certains templates. */
        couleurDomaine(nomDomaine) {
            return this.domaineBadgeClass(nomDomaine);
        },

        /** Ouvre la modale de création et réinitialise le formulaire. */
        basculerModeSelection() {
            this.modeSelection = !this.modeSelection;
            this.selectionnees = [];
        },
        toggleSelection(id) {
            this.selectionnees = this.selectionnees.includes(id) ? this.selectionnees.filter(item => item !== id) : [...this.selectionnees, id];
        },
        toggleSelectionGlobale() {
            const visibles = this.formationsFiltrees().map(formation => formation.id);
            const tousSelectionnes = visibles.length > 0 && visibles.every(id => this.selectionnees.includes(id));
            this.selectionnees = tousSelectionnes ? this.selectionnees.filter(id => !visibles.includes(id)) : [...new Set([...this.selectionnees, ...visibles])];
        },
        async supprimerSelection() {
            if (!this.selectionnees.length || !await window.demanderConfirmation(`${this.selectionnees.length} formation(s) sélectionnée(s) seront définitivement supprimée(s).`)) return;
            try {
                const res = await fetch(urlFormations, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ ids: this.selectionnees }) });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.erreur || 'Suppression impossible.');
                this.formations = this.formations.filter(formation => !this.selectionnees.includes(formation.id));
                this.modeSelection = false; this.selectionnees = [];
                window.afficherToast?.('succes', `${data.supprimees.length} formation(s) supprimée(s).`);
            } catch (err) { window.afficherToast?.('erreur', err.message); }
        },

        ouvrirModaleCreation() {
            this.formulaire = { titre: '', domaine_id: '', duree_jours: 3, description: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        /** Ferme la modale de création si aucune requête n'est en cours. */
        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

        /**
         * Soumet la création d'une nouvelle formation via POST.
         * @returns {Promise<void>}
         */
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlFormations, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        titre: this.formulaire.titre,
                        domaine_id: this.formulaire.domaine_id,
                        duree_jours: this.formulaire.duree_jours,
                        description: this.formulaire.description || null,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formation créée avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur création formation :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
            }
        },

        /**
         * Ouvre la modale d'édition pré-remplie avec les données de la formation sélectionnée.
         * @param {object} formation Objet formation de la liste.
         */
        ouvrirModaleEdition(formation) {
            this.edition = {
                id: formation.id,
                titre: formation.titre,
                domaine_id: formation.domaine?.id ?? '',
                duree_jours: formation.duree_jours,
                description: formation.description || '',
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
         * Soumet les modifications de la formation via PUT.
         * @returns {Promise<void>}
         */
        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlFormations}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        titre: this.edition.titre,
                        domaine_id: this.edition.domaine_id,
                        duree_jours: this.edition.duree_jours,
                        description: this.edition.description || null,
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
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formation modifiée avec succès.');
                await this.appliquerFiltres(false);
            } catch (err) {
                console.error('Erreur modification formation :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },

        /**
         * Ouvre la modale de confirmation de suppression pour une formation.
         * @param {object} formation Formation à supprimer.
         */
        ouvrirModaleSuppression(formation) {
            this.aSupprimer = formation;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        /** Ferme la modale de suppression si aucune requête n'est en cours. */
        fermerModaleSuppression() {
            if (!this.suppressionEnCours) {
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;
            }
        },

        /**
         * Confirme la suppression de la formation via DELETE.
         * Un statut 409 indique l'existence de sessions associées (bloquant).
         * @returns {Promise<void>}
         */
        async confirmerSuppression() {
            this.suppressionEnCours = true;
            this.erreurSuppression = null;

            try {
                const res = await fetch(`${urlFormations}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (res.status === 204) {
                    this.modaleSuppressionOuverte = false;
                    this.aSupprimer = null;
                    if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Formation supprimée avec succès.');
                    await this.appliquerFiltres(false);
                    return;
                }

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Erreur inattendue du serveur.' };
                }
                this.erreurSuppression = data.erreur || 'Impossible de supprimer cette formation.';
                if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurSuppression);

            } catch (err) {
                console.error('Erreur suppression formation :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
            }
        },
    };
}

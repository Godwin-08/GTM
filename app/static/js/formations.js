const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

function pageFormationsData() {
    return {
        formations: [],
        domaines: [],
        chargementEnCours: true,
        erreur: null,
        filtres: {
            q: '',
            domaine_id: '',
            tri: '',
        },
        modaleOuverte: false,
        envoiEnCours: false,
        erreurFormulaire: null,
        formulaire: { titre: '', domaine_id: '', duree_jours: 3, description: '' },
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: { id: null, titre: '', domaine_id: '', duree_jours: 3, description: '' },
        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.q = params.get('q') || '';
            this.filtres.domaine_id = params.get('domaine_id') || '';
            this.filtres.tri = params.get('tri') || '';
        },

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

        reinitialiserFiltres() {
            this.filtres = { q: '', domaine_id: '', tri: '' };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        formationsFiltrees() {
            const copie = [...this.formations];
            const t = this.filtres.tri;
            if (t === 'titre_desc') return copie.sort((a, b) => b.titre.localeCompare(a.titre));
            if (t === 'duree_desc') return copie.sort((a, b) => b.duree_jours - a.duree_jours);
            if (t === 'duree_asc') return copie.sort((a, b) => a.duree_jours - b.duree_jours);
            if (t === 'domaine_asc') return copie.sort((a, b) => (a.domaine?.nom || '').localeCompare(b.domaine?.nom || ''));
            return copie.sort((a, b) => a.titre.localeCompare(b.titre));
        },

        nomDomaine(formation) {
            return formation.domaine?.nom || '';
        },

        couleurDomaine(nomDomaine) {
            return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600';
        },

        ouvrirModaleCreation() {
            this.formulaire = { titre: '', domaine_id: '', duree_jours: 3, description: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        fermerModaleCreation() {
            if (!this.envoiEnCours) this.modaleOuverte = false;
        },

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

        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

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

        ouvrirModaleSuppression(formation) {
            this.aSupprimer = formation;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
            this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
        },

        fermerModaleSuppression() {
            if (!this.suppressionEnCours) {
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;
            }
        },

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

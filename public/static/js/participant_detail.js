// ============================================================
// Page /participants/<id> : détail d'un participant,
// avec la liste de ses inscriptions aux sessions.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const COULEURS_STATUT_INSCRIPTION = {
    'confirmee': { classe: 'bg-success/10 text-success', label: 'Confirmée' },
    'liste_attente': { classe: 'bg-warning/10 text-warning', label: "Liste d'attente" },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

function pageParticipantDetailData(participantId) {
    return {
        participant: null,
        inscriptions: [],
        modeSelection: false,
        selectionnees: [],
        suppressionEnCours: false,
        chargementEnCours: true,
        erreur: null,

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const [resParticipant, resInscriptions] = await Promise.all([
                    fetch(`/api/participants/${participantId}`),
                    fetch(`/api/inscriptions?participant_id=${participantId}`),
                ]);

                if (!resParticipant.ok) throw new Error('Participant introuvable');
                this.participant = await resParticipant.json();

                if (resInscriptions.ok) {
                    this.inscriptions = await resInscriptions.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail participant :', err);
                this.erreur = 'Impossible de charger ce participant.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        formaterDate(dateStr) {
            if (!dateStr) return '—';
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]} ${d.getFullYear()}`;
        },

        labelInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { label: statut }).label;
        },
        classeBadgeInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },

        basculerModeSelection() {
            this.modeSelection = !this.modeSelection;
            this.selectionnees = [];
        },

        toggleSelection(id) {
            if (this.selectionnees.includes(id)) {
                this.selectionnees = this.selectionnees.filter(item => item !== id);
            } else {
                this.selectionnees = [...this.selectionnees, id];
            }
        },

        toggleSelectionGlobale() {
            if (this.selectionnees.length === this.inscriptions.length) {
                this.selectionnees = [];
            } else {
                this.selectionnees = this.inscriptions.map(i => i.id);
            }
        },

        async supprimerInscription(inscriptionId) {
            const inscription = this.inscriptions.find(i => i.id === inscriptionId);
            const nomSession = inscription?.session?.formation?.titre || 'cette session';

            if (!await window.demanderConfirmation(
                `L'inscription de ${this.participant?.nom || 'ce participant'} à ${nomSession} sera définitivement supprimée.`
            )) {
                return;
            }

            try {
                const res = await fetch(`/api/inscriptions/${inscriptionId}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.erreur || 'Impossible de supprimer cette inscription.');
                }

                this.inscriptions = this.inscriptions.filter(i => i.id !== inscriptionId);
                this.selectionnees = this.selectionnees.filter(id => id !== inscriptionId);

                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('succes', 'Inscription supprimée avec succès.');
                }
            } catch (err) {
                console.error('Erreur suppression inscription :', err);
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', err.message || 'Erreur lors de la suppression.');
                } else {
                    alert(err.message || 'Erreur lors de la suppression.');
                }
            } finally {
                this.$nextTick(() => lucide.createIcons());
            }
        },

        async supprimerSelection() {
            if (this.selectionnees.length === 0) return;

            const ok = await window.demanderConfirmation(
                `${this.selectionnees.length} inscription(s) sélectionnée(s) seront définitivement supprimées.`
            );
            if (!ok) return;

            this.suppressionEnCours = true;
            try {
                const res = await fetch('/api/inscriptions', {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: this.selectionnees }),
                });

                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    throw new Error(data.erreur || 'Impossible de supprimer les inscriptions sélectionnées.');
                }

                this.inscriptions = this.inscriptions.filter(i => !this.selectionnees.includes(i.id));
                this.selectionnees = [];

                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('succes', `${data.supprimees?.length || 0} inscription(s) supprimée(s).`);
                }
            } catch (err) {
                console.error('Erreur suppression sélection :', err);
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', err.message || 'Erreur lors de la suppression.');
                } else {
                    alert(err.message || 'Erreur lors de la suppression.');
                }
            } finally {
                this.suppressionEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },
    };
}


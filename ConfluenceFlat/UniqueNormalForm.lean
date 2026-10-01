import ConfluenceFlat.Core

namespace ConfluenceFlat

namespace FiniteARS

universe u

def Confluent {α : Type u} (R : RewriteSystem α) : Prop :=
  ∀ ⦃a b c : α⦄, Reachable R a b → Reachable R a c → Joinable R b c

def Normalizing {α : Type u} (R : RewriteSystem α) : Prop :=
  ∀ a, ∃ n, Reachable R a n ∧ NormalForm R n

def UniqueNormalFormFrom {α : Type u} (R : RewriteSystem α) (a : α) : Prop :=
  ∀ b c,
    Reachable R a b → NormalForm R b →
    Reachable R a c → NormalForm R c →
    b = c

def ExistsUniqueNormalFormFrom {α : Type u} (R : RewriteSystem α) (a : α) : Prop :=
  ∃ n,
    Reachable R a n ∧
    NormalForm R n ∧
    ∀ m, Reachable R a m → NormalForm R m → m = n

theorem reachable_eq_of_normalForm {α : Type u} {R : RewriteSystem α} {a b : α}
    (hna : NormalForm R a) (hab : Reachable R a b) : a = b := by
  induction hab with
  | refl _ => rfl
  | tail hstep _ _ =>
      exact False.elim (hna _ hstep)

theorem eq_of_joinable_normalForms {α : Type u} {R : RewriteSystem α} {b c : α}
    (hjoin : Joinable R b c)
    (hnb : NormalForm R b)
    (hnc : NormalForm R c) : b = c := by
  rcases hjoin with ⟨w, hbw, hcw⟩
  have hbw : b = w := reachable_eq_of_normalForm hnb hbw
  have hcw' : c = w := reachable_eq_of_normalForm hnc hcw
  calc
    b = w := hbw
    _ = c := hcw'.symm

theorem uniqueNormalFormFrom_of_confluent {α : Type u} {R : RewriteSystem α}
    (hconf : Confluent R) (a : α) :
    UniqueNormalFormFrom R a := by
  intro b c hab hnb hac hnc
  exact eq_of_joinable_normalForms (hconf hab hac) hnb hnc

theorem existsUniqueNormalFormFrom_of_confluent_normalizing {α : Type u} {R : RewriteSystem α}
    (hconf : Confluent R) (hnorm : Normalizing R) (a : α) :
    ExistsUniqueNormalFormFrom R a := by
  rcases hnorm a with ⟨n, han, hnnf⟩
  refine ⟨n, han, hnnf, ?_⟩
  intro m ham hmnf
  exact (uniqueNormalFormFrom_of_confluent hconf a) m n ham hmnf han hnnf

end FiniteARS

end ConfluenceFlat

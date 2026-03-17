namespace ConfluenceFlat

namespace FiniteARS

universe u

structure ARS (α : Type u) where
  states : List α
  step : α → α → Prop
  step_closed : ∀ {a b}, step a b → a ∈ states ∧ b ∈ states

inductive Reachable {α : Type u} (R : ARS α) : α → α → Prop
  | refl (a : α) : Reachable R a a
  | tail {a b c : α} : R.step a b → Reachable R b c → Reachable R a c

def Joinable {α : Type u} (R : ARS α) (a b : α) : Prop :=
  ∃ c, Reachable R a c ∧ Reachable R b c

def NormalForm {α : Type u} (R : ARS α) (a : α) : Prop :=
  ∀ b, ¬ R.step a b

def LocalConfluent {α : Type u} (R : ARS α) : Prop :=
  ∀ ⦃a b c : α⦄, R.step a b → R.step a c → Joinable R b c

def ElementaryPeak {α : Type u} (R : ARS α) (a b c : α) : Prop :=
  R.step a b ∧ R.step a c ∧ b ≠ c

def ElementaryFlat {α : Type u} (R : ARS α) : Prop :=
  ∀ ⦃a b c : α⦄, ElementaryPeak R a b c → Joinable R b c

theorem joinable_refl {α : Type u} (R : ARS α) (a : α) : Joinable R a a := by
  exact ⟨a, Reachable.refl (R := R) a, Reachable.refl (R := R) a⟩

theorem elementaryFlat_of_localConfluent {α : Type u} {R : ARS α}
    (h : LocalConfluent R) : ElementaryFlat R := by
  intro a b c hpeak
  exact h hpeak.1 hpeak.2.1

theorem localConfluent_of_elementaryFlat {α : Type u} {R : ARS α}
    (h : ElementaryFlat R) : LocalConfluent R := by
  intro a b c hab hac
  by_cases hEq : b = c
  · cases hEq
    exact joinable_refl R b
  · exact h ⟨hab, hac, hEq⟩

theorem elementaryFlat_iff_localConfluent {α : Type u} (R : ARS α) :
    ElementaryFlat R ↔ LocalConfluent R := by
  constructor
  · intro h
    exact localConfluent_of_elementaryFlat h
  · intro h
    exact elementaryFlat_of_localConfluent h

end FiniteARS

end ConfluenceFlat

import ConfluenceFlat.UniqueNormalForm

namespace ConfluenceFlat.FiniteARS

universe u

/-- Well-foundedness in the direction of reduction, not its converse. -/
def Terminating {α : Type u} (R : RewriteSystem α) : Prop :=
  WellFounded (fun b a => R.step a b)

theorem normalizing_of_terminating {α : Type u} {R : RewriteSystem α}
    (ht : Terminating R) : Normalizing R := by
  classical
  intro a
  induction a using ht.induction with
  | h a ih =>
    by_cases hs : ∃ b, R.step a b
    · obtain ⟨b, hab⟩ := hs
      obtain ⟨n, hbn, hnf⟩ := ih b hab
      exact ⟨n, Reachable.tail hab hbn, hnf⟩
    · exact ⟨a, Reachable.refl a, fun b hab => hs ⟨b, hab⟩⟩

/-- Newman's lemma, with no finiteness hypothesis. -/
theorem confluent_of_terminating_localConfluent {α : Type u} {R : RewriteSystem α}
    (ht : Terminating R) (hl : LocalConfluent R) : Confluent R := by
  intro a
  induction a using ht.induction with
  | h a ih =>
    intro b c hab hac
    cases hab with
    | refl _ => exact ⟨c, hac, Reachable.refl c⟩
    | @tail _ b₁ _ hab₁ hb₁b =>
      cases hac with
      | refl _ => exact ⟨b, Reachable.refl b, Reachable.tail hab₁ hb₁b⟩
      | @tail _ c₁ _ hac₁ hc₁c =>
        obtain ⟨d, hb₁d, hc₁d⟩ := hl hab₁ hac₁
        obtain ⟨v, hcv, hdv⟩ := ih c₁ hac₁ hc₁c hc₁d
        obtain ⟨w, hbw, hvw⟩ := ih b₁ hab₁ hb₁b (hb₁d.trans hdv)
        exact ⟨w, hbw, hcv.trans hvw⟩

theorem confluent_iff_elementaryFlat_of_terminating {α : Type u} {R : RewriteSystem α}
    (ht : Terminating R) : Confluent R ↔ ElementaryFlat R := by
  constructor
  · intro hc a b c hp
    exact hc (Reachable.tail hp.1 (Reachable.refl b))
      (Reachable.tail hp.2.1 (Reachable.refl c))
  · intro hf
    exact confluent_of_terminating_localConfluent ht
      (localConfluent_of_elementaryFlat hf)

/-- Weak normalization suffices for the converse normal-form criterion. -/
theorem confluent_of_normalizing_uniqueNormalForms {α : Type u} {R : RewriteSystem α}
    (hn : Normalizing R) (hu : ∀ a, UniqueNormalFormFrom R a) : Confluent R := by
  intro a b c hab hac
  obtain ⟨n, hbn, hnf⟩ := hn b
  obtain ⟨m, hcm, hmf⟩ := hn c
  have heq := hu a n m (hab.trans hbn) hnf (hac.trans hcm) hmf
  cases heq
  exact ⟨n, hbn, hcm⟩

theorem confluent_iff_uniqueNormalForms_of_normalizing {α : Type u} {R : RewriteSystem α}
    (hn : Normalizing R) : Confluent R ↔ ∀ a, UniqueNormalFormFrom R a := by
  exact ⟨fun hc a => uniqueNormalFormFrom_of_confluent hc a,
    confluent_of_normalizing_uniqueNormalForms hn⟩

theorem existsUniqueNormalFormFrom_of_terminating_elementaryFlat
    {α : Type u} {R : RewriteSystem α} (ht : Terminating R) (hf : ElementaryFlat R) (a : α) :
    ExistsUniqueNormalFormFrom R a := by
  exact existsUniqueNormalFormFrom_of_confluent_normalizing
    ((confluent_iff_elementaryFlat_of_terminating ht).mpr hf)
    (normalizing_of_terminating ht) a

end ConfluenceFlat.FiniteARS

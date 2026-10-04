export type Decimal = string;
export interface Page<T> { results: T[]; count: number; next: string | null }
export interface Named { id: string; name?: string; display_name?: string; title?: string }
export interface Category extends Named { name: string; slug?: string }
export interface Profile { university?: string; department?: string; bio?: string; skills?: string[]; hourly_rate?: Decimal; photo?: string; portfolio_links?: { title: string; url: string; kind: string }[] }
export interface Verification { student?: { status?: string; verified_until?: string; student_email?: string }; employer?: { status?: string; kind?: string }; phone?: { status?: string }; payment?: { status?: string; provider_ready?: boolean; provider_verified?: boolean } }
export interface User extends Named { email: string; roles: string[]; is_staff: boolean; profile?: Profile; verification?: Verification; preferences?: { in_app: boolean; email: boolean } }
export interface PublicProfile extends Named, Profile { user?: string; profile?: Profile }
export interface Config { mode: string; payment_provider: string; payment_ready: boolean; payment_requires_buyer: boolean; payout_ready: boolean; production_readiness_missing: string[]; verification_required: boolean; credit_policy: Record<string, string | number | null>; tracker_policy: { idle_seconds?: number | null; preview_seconds?: number | null }; categories: Category[]; readiness?: { missing?: string[] } }
export interface Attachment extends Named { filename?: string; size?: number }
export interface Job extends Named { owner: string; owner_name: string; title: string; description: string; category: string; skills: string[]; work_type: "fixed" | "hourly"; budget: Decimal; expected_duration: string; deadline?: string; status: string; created_at: string; boosted_until?: string; attachments?: Attachment[] }
export interface Application extends Named { job: string; student: string; student_name?: string; team?: string; team_name?: string; job_title?: string; cover_letter: string; price: Decimal; duration: string; sample_url?: string; status: string; conversation: string; created_at: string; boosted_until?: string }
export interface Invitation extends Named { job: string; job_title?: string; student?: string; team?: string; status: string; conversation?: string }
export interface TeamMember { user: string; display_name: string; status: string }
export interface Team extends Named { name: string; description: string; leader: string; members: TeamMember[]; wallet_id: string; leader_changes?: LeaderChange[]; active_contract_ids?: string[] }
export interface LeaderChange extends Named { new_leader_name?: string; payee_name?: string; admin_approved?: boolean; team: string; new_leader: string; payee: string; reason: string; status: string; contract_ids?: string[]; approved_by?: string[] }
export interface Milestone extends Named { title: string; amount: Decimal; status: string; submission?: { text?: string; attachments?: Attachment[] } | string; submitted_at?: string; review_due_at?: string }
export interface Week extends Named { contract: string; starts_at: string; ends_at: string; status: string; limit_hours: Decimal; reserved_amount: Decimal; worked_seconds: number; gross: Decimal; net: Decimal; review_due_at?: string }
export interface ContractMember { user: string; hourly_rate: Decimal; display_name?: string }
export interface MilestoneTerms { id?: string; title: string; amount: Decimal }
export interface ContractTerms { scope: string; revision_terms: string; expected_duration: string; tracker_required: boolean; rate: Decimal; weekly_limit: Decimal; members: ContractMember[]; milestones: MilestoneTerms[] }
export interface ContractChange extends Named { contract?: string; proposer?: string; terms?: Partial<ContractTerms>; created_at?: string; status: string; accepted_by?: string[] }
export interface Contract extends Named { stale_team_leader: boolean; current_team_leader: {id:string;display_name:string}|null; job: string; job_title?: string; application: string; employer: string; freelancer: string; team?: string; payee: string; status: string; scope: string; work_type: "fixed" | "hourly"; rate: Decimal; weekly_limit: Decimal; expected_duration: string; revision_terms: string; tracker_required: boolean; members: { user: string; hourly_rate: Decimal; display_name?: string }[]; milestones: Milestone[]; accepted_by: string[]; conversation: string; changes?: ContractChange[]; leader_changes?: LeaderChange[] }
export interface ManualTime extends Named { starts_at: string; ends_at: string; memo: string; status: string; owner?: string; owner_name?: string; worker?: string; worker_name?: string; seconds?: number }
export interface LedgerEntry extends Named { amount?: Decimal | number; balance?: Decimal | number; delta?: Decimal | number; balance_after?: Decimal | number; kind?: string; reference?: string; reason?: string; description?: string; created_at?: string; event_type?: string }
export interface CreditWallet extends Named { team?: string; balance: number; entries: LedgerEntry[]; mode: string }
export interface Payment extends Named { attempt: number; retry_allowed: boolean; mode: "simulator" | "iyzico_sandbox" | "iyzico_live"; target_type: string; target_id: string; amount: Decimal; currency: "TRY"; status: string; checkout_url?: string; checkout_expires_at?: string; provider_reference?: string; funded_at?: string; released_amount: Decimal; refunded_amount: Decimal; settlement_status: string; error_code?: string }
export interface Payout extends Named { bank_transfer_proven: boolean; mode: string; amount: Decimal; currency: "TRY"; account_name: string; iban_masked: string; status: string; reserved_amount: Decimal; provider_reference?: string; requested_at: string; paid_at?: string; failure_reason?: string }
export interface Money { currency: "TRY"; available: Decimal; reserved: Decimal; pending: Decimal; payouts: Payout[]; entries?: LedgerEntry[] }
export interface Screenshot { id: string; state: "preview" | "held" | "released" | "withheld"; captured_at: string; privacy_request?: string; publication_ready_at?: string; review_due_at?: string }
export interface Block extends Named { client_id: string; session: string; contract: string; owner: string; owner_name?: string; starts_at: string; ends_at: string; seconds: number; key_count: number; mouse_count: number; active_app: string; memo?: string; screenshot?: Screenshot }
export interface Message extends Named { text: string; sender: string; sender_name?: string; created_at: string; attachments?: Attachment[] }
export interface Conversation extends Named { title?: string; job_title?: string; contract?: string; messages?: Message[]; participants?: Named[] }
export interface Notice extends Named { title: string; body?: string; message?: string; created_at: string; read_at?: string; is_read?: boolean; url?: string; resource_type?: string; resource_id?: string; event?: string }
export interface Dispute extends Named { contract: string; milestone?: string; week?: string; reason: string; status: string; resolution?: string; created_at?: string }
export interface Rating extends Named { score: number; comment: string; author?: string; author_name?: string; created_at?: string }
export interface University extends Named { name: string; domains: string[] }
export interface Case extends Named { target_type?: string; target_id?: string; attempt?: number; retry_allowed?: boolean; released_amount?: Decimal; refunded_amount?: Decimal; settlement_status?: string; state?: string; error_code?: string; missing_operation?: string; attempts?: number; reserved_seconds?: number; used_seconds?: number; authorized_until?: string; funding?: {week?:string;milestone?:string;reserved_amount?:Decimal}; starts_at?: string; ends_at?: string; seconds?: number; memo?: string; mode?: string; bank_transfer_proven?: boolean; milestone?: string; week?: string; kind?: string; type?: string; status: string; reason?: string; contract?: string; screenshot?: string; user?: string; team?: string; payment?: string; amount?: Decimal; job?: string; owner_name?: string; display_name?: string; legal_name?: string; company_name?: string; job_title?: string; purchase?: string; wallet?: string; credits?: number; owner?: string; created_at?: string; new_leader_name?: string; payee_name?: string; account_name?: string; iban_masked?: string; phone_verified?: boolean; identity_reference?: string; company_reference?: string; authorized_reference?: string }
export interface Audit extends Named { actor?: string; resource?: string; action?: string; reason?: string; resource_type?: string; resource_id?: string; outcome?: string; created_at?: string }
export type Queue = Record<string, Case[]>;

export interface Worklog { milestones: Milestone[]; blocks: Block[]; manual_time: ManualTime[]; weeks: Week[]; summary: { basis: "fixed_target_amount"|"hourly_worked_amount"; seconds: number; gross: Decimal; net: Decimal; currency: "TRY" } }
export interface CreditPurchase extends Named { wallet: string; credits: number; amount: Decimal; status: string; payment: string | null }

export interface PublicTeam extends Named { name: string; description: string; leader_name: string }

export interface TeamInvitation extends Named { name: string; description: string; leader_name: string; membership_status: "invited" }

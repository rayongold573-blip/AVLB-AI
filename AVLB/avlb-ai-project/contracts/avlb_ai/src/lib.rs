use anchor_lang::prelude::*;

declare_id!("AVLB111111111111111111111111111111111111111");

#[program]
pub mod avlb_ai {
    use super::*;

    pub fn register_validator(ctx: Context<RegisterValidator>, name: String) -> Result<()> {
        let v = &mut ctx.accounts.validator_info;
        v.name = name;
        v.is_active = true;
        v.last_update = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn update_metrics(ctx: Context<UpdateMetrics>, latency: u64, load: u8) -> Result<()> {
        let v = &mut ctx.accounts.validator_info;
        v.latency = latency;
        v.load_percent = load;
        v.last_update = Clock::get()?.unix_timestamp;
        Ok(())
    }
}

#[account]
pub struct ValidatorInfo {
    pub name: String,
    pub latency: u64,
    pub load_percent: u8,
    pub last_update: i64,
    pub is_active: bool,
}

#[derive(Accounts)]
pub struct RegisterValidator<'info> {
    #[account(init, payer = user, space = 8 + 40 + 8 + 1 + 8 + 1)]
    pub validator_info: Account<'info, ValidatorInfo>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateMetrics<'info> {
    #[account(mut)]
    pub validator_info: Account<'info, ValidatorInfo>,
}
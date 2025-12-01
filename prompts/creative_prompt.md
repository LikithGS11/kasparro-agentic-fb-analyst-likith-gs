# Creative Generator Logic

The Creative Agent generates template-based recommendations for campaigns with low CTR.

## Logic Overview
- Identifies campaigns with CTR drops from the summary data
- Uses predefined headline templates with campaign name substitution
- Uses predefined message templates with campaign name substitution
- Selects CTA deterministically based on campaign name hash and config seed

## Template Categories
- Headlines: Limited time offers, deal announcements, new arrival notifications
- Messages: Discount exclusivity, product quality, bundle promotions
- CTAs: Shop Now, Buy Today, Explore Deals

## Deterministic Selection
- CTA selection uses hash(campaign_name + seed) % len(options) for reproducibility
- No randomness - same input always produces same output

## Output Structure
Returns JSON with creatives array containing campaign-specific recommendations.

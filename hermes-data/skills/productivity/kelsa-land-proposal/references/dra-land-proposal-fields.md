# DRA Land Proposal — Field Identifier Reference

Pipeline: DRA Land Proposal (ID: 519) in account DRA (ID: 5).
URL: https://kelsa.io/519

## Stages (10)

| Name | Identifier | Type |
|------|-----------|------|
| Proposed | st_proposed | Active (entry) |
| Info Gathered | st_info_gathered | Active |
| Initial Feasibility Checked | st_feasibility_approval_taken | Active |
| Site Visited And Approved | st_site_visited_and_approved | Active |
| Proposal Made | st_proposal_made | Active |
| Commercial Closure & Token Done | st_commercial_closure___token_done | Active |
| Legal Ok Obtained | st_legal_ok_obtained | Active |
| Agreement Done | st_agreement_done | Active |
| Lost Opportunity | st_lost_opportunity | Retired |
| Rejected | st_rejected | Retired |

## Fields by field set

### Land Details (cf_)
| Field | Identifier | Type |
|-------|-----------|------|
| Land Location | cf_land_location | location |
| City | cf_city | dropdown (7 opt) |
| Land Size UoM | cf_land_size_uom | dropdown (8 opt: Acres, Sqft, etc.) |
| Land Size Acres | cf_land_size_acres | number (use for land; for built-up use Sqft instead) |
| Land Size Guntas | cf_land_size_guntas | number |
| Land Size Cents | cf_land_size_cents | number |
| Land Size Grounds | cf_land_size_grounds | number |
| Land Size Sqmt | cf_land_size_sqmt | number |
| Land Size Sqft (2x) | cf_land_size_sqft / cf_land_size | number |
| Land Size Base | cf_land_size_base | number |
| Location Google MapLink | cf_location_google_maplink | attachment (accepts URL string) |
| Adjoining Road Width | cf_adjoining_road_width | number |
| Other details | cf_other_details | text |
| Land Status On Offer | cf_status_on_offer | dropdown (5 opt) |
| Land Zone | cf_land_zone | dropdown (5 opt) |
| FAR Applicable | cf_far_applicable | number |
| Land Sketch | cf_land_sketch | attachment (single file) |
| Land Legal Set | cf_land_legal_set | attachment |
| Land pics | cf_land_pics | attachment (multi-file — videos + images) |
| Revenue Maps And Documents | cf_revenue_maps_and_documents | attachment |
| Key Legal Points to Cover | cf_key_legal_points_to_cover | text |
| Sy Nos | cf_sy_nos | text (comma-separated) |
| Village | cf_village | text |
| Hobli | cf_hobli | text |
| Taluk | cf_taluk | text |
| District | cf_district | text |
| Land notes | cf_land_notes | text |

### Proposal Details (cf_)
| Field | Identifier | Type |
|-------|-----------|------|
| Date of Proposal | cf_date_of_proposal | date |
| Proposal Brief | cf_name | text |
| Proposal Source | cf_proposal_source | dropdown (88 opt — broker names) |
| Proposal Source Details Notes | cf_proposal_source_details_notes | text |
| Correspondence Email | cf_correspondence_email | email |
| Offer Type | cf_offer_type | dropdown (8 opt: Outright, JV, Mix, etc.) |
| Expected Rate Per Sqft for Outright | cf_expected_rate_per_sqft | number (₹) |
| Expected Total Outright Cost of Land | cf_expected_total_outright_cost_of_land | number (₹) |
| Expected JV Ratio for Land Owner | cf_expected_jv_ratio | number (%) |
| Expected JV Ratio for Developer | cf_expected_jv_ratio_for_developer | number (%) |
| Expected Refundable per sqft | cf_expected_refundable | number (₹) |
| Expected Total Refundable Amount | cf_expected_total_refundable_amount | number (₹) |
| Expected Goodwill per sqft | cf_expected_goodwill | number (₹) |
| Expected Total Non-Refundable Amount | cf_expected_total_non_refundable_amount | number (₹) |
| Product Type | cf_product_type | dropdown (12 opt: Villa, Row House, Plots, Commercial, Apartment - High Rise (>G+8), Farm Plots, etc.) |
| Proposal Notes | cf_proposal_notes | text (HTML supported) |
| Total Upfront Investment Expected | cf_total_upfront_investment_expected | number (₹) |
| Expected Total Built-up Area In Sqft | cf_expected_total_built_up_area_in_sqft | number |
| Expected Total Upfront Investment | cf_expected_total_upfront_investment | number (₹) |

### Market Data (cf_)
| Field | Identifier | Type |
|-------|-----------|------|
| Location Pics | cf_location_pics | attachment |
| RnD Data | cf_rnd_data1 | tabular |
| Competitor Data | cf_competitor_data | attachment |

### Financial Evaluation Data (cf_)
| Field | Identifier | Type |
|-------|-----------|------|
| FAR Land Cost | cf_far_land_cost | number |
| Construction Cost | cf_construction_cost | number |
| Landed Product Cost | cf_landed_product_cost | number |
| Min Selling Price | cf_min_selling_price | number |
| Max Selling Price | cf_max_selling_price | number |
| Project Duration | cf_project_duration | number |
| Expected Min IRR | cf_expected_min_irr | number (%) |
| Expected MAX IRR | cf_expected_max_irr | number (%) |
| Average unit size | cf_average_unit_size | number |
| Detailed Financial Workings | cf_detailed_financial_workings | attachment |
| BHK Inventory Overhang + Sales Velocity | cf_*bhk_* (8 fields) | number |
| Competitor's data | cf_direct_competitor_s_* (3 fields) | number |

### Offer Details (cf_offered_*)
| Field | Identifier | Type |
|-------|-----------|------|
| Offered JV Refundable (per sqft) | cf_offered_jv_refundable | number |
| Offered Type | cf_offered_type | dropdown (5 opt) |
| Offered JV Non-Refundable | cf_offered_jv_non_refundable | number |
| Offered JV Refundable Total | cf_offered_jv_refundable_total | number |
| Offered JV Non-Refundable Total | cf_offered_jv_non_refundable_total | number |
| Offered Built-up Area Ratio (LO) | cf_offered_built_up_area_ratio_to_land_owner | number |
| Offered Built-up Area Ratio (Dev) | cf_offered_built_up_area_ratio_for_developer | number |
| Offered Total JV Outflow | cf_offered_total_jv_outflow | number |
| Offered Outright Rate | cf_offered_outright_rate | number |
| Offered Total Outright Price | cf_offered_total_outright_price | number |
| Offer Document | cf_offer_document | attachment |

### Ungrouped (no field set)
| Field | Identifier | Type |
|-------|-----------|------|
| ProposalID | cf_proposalid | text (auto-generated?) |
| Additional Team Member | cf_additional_team_member | user |
| Date of RnD Record | cf_date | date |
| Project name | cf_project_name1 | text |
| Project location | cf_project_location | attachment |
| Project type | cf_project_type | dropdown (4 opt) |
| Contact information | cf_contact_information | contact |
| Website link | cf_website_link | attachment |
| Project images | cf_project_images | attachment |
| comments | cf_comments | text |

## Built-up / Commercial property notes

This pipeline is named "Land Proposal" but has been used for **built-up commercial properties** too. For those:
- Skip `cf_land_size_acres`/guntas/grounds — use `cf_land_size_uom: "Sqft"` + `cf_land_size_sqft` for total site area
- Use `cf_expected_total_built_up_area_in_sqft` for leasable/saleable built-up area
- Use `cf_product_type: "Commercial"` (no "Office" option exists — use "Commercial")
- Use `cf_land_location`, `cf_village`, `cf_hobli`, `cf_taluk`, `cf_district` for the building's address area
- `cf_land_zone` can be "Commercial" for zoned land under the building
- The existing financial fields work directly (rate per sqft, total cost, upfront investment)

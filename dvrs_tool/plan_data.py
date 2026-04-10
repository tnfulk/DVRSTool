"""Technical plan definitions and regulatory policy helpers."""

from __future__ import annotations

from .models import BandFamily, Country, RegulatoryStatus, TechnicalPlan


TECHNICAL_PLANS: dict[BandFamily, list[TechnicalPlan]] = {
    BandFamily.BAND_700: [
        TechnicalPlan(
            id="700-A",
            display_name="700 MHz In-Band Plan A",
            band_family=BandFamily.BAND_700,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(799.0, 805.0),
            dvrs_tx_window=(769.0, 775.0),
            pair_offset_mhz=30.0,
            pair_direction="tx_below_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(806.0, 824.0),
            active_mobile_rx_window=(851.0, 869.0),
            system_800_rx_range=(851.0, 869.0),
            system_800_tx_range=(806.0, 824.0),
            fixed_dvrs_tx_range=(769.0, 775.0),
            fixed_dvrs_rx_range=(799.0, 805.0),
            notes=["Supports the standard 700 MHz in-band Plan A duplex layout."],
        ),
        TechnicalPlan(
            id="700-B",
            display_name="700 MHz In-Band Plan B",
            band_family=BandFamily.BAND_700,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(799.0, 802.0),
            dvrs_tx_window=(769.0, 772.0),
            pair_offset_mhz=30.0,
            pair_direction="tx_below_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(802.0, 805.0),
            active_mobile_rx_window=(772.0, 775.0),
            system_700_rx_range=(772.0, 775.0),
            system_700_tx_range=(802.0, 805.0),
            system_800_rx_range=(851.0, 869.0),
            system_800_tx_range=(806.0, 824.0),
            fixed_dvrs_tx_range=(769.0, 772.0),
            fixed_dvrs_rx_range=(799.0, 802.0),
            notes=["Supports the standard 700 MHz in-band Plan B duplex layout."],
        ),
        TechnicalPlan(
            id="700-C",
            display_name="700 MHz In-Band Plan C",
            band_family=BandFamily.BAND_700,
            dvrs_mode="duplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(802.0, 805.0),
            dvrs_tx_window=(772.0, 775.0),
            pair_offset_mhz=30.0,
            pair_direction="tx_below_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(799.0, 802.0),
            active_mobile_rx_window=(769.0, 772.0),
            system_700_rx_range=(769.0, 772.0),
            system_700_tx_range=(799.0, 802.0),
            system_800_rx_range=(851.0, 869.0),
            system_800_tx_range=(806.0, 824.0),
            fixed_dvrs_tx_range=(772.0, 775.0),
            fixed_dvrs_rx_range=(802.0, 805.0),
            notes=["Supports the standard 700 MHz in-band Plan C duplex layout."],
        ),
    ],
    BandFamily.BAND_800: [
        TechnicalPlan(
            id="800-A1",
            display_name="800 MHz In-Band Plan A1",
            band_family=BandFamily.BAND_800,
            dvrs_mode="duplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(816.0, 824.0),
            dvrs_tx_window=(861.0, 869.0),
            pair_offset_mhz=45.0,
            pair_direction="tx_above_rx",
            min_separation_from_mobile_tx_mhz=5.0,
            min_separation_from_mobile_rx_mhz=5.0,
            max_dvrs_passband_mhz=3.0,
            active_mobile_tx_window=(806.0, 819.0),
            active_mobile_rx_window=(851.0, 864.0),
            system_700_rx_range=(764.0, 775.0),
            system_700_tx_range=(794.0, 805.0),
            system_800_rx_range=(851.0, 864.0),
            system_800_tx_range=(806.0, 819.0),
            fixed_dvrs_tx_range=(861.0, 869.0),
            fixed_dvrs_rx_range=(816.0, 824.0),
            notes=["Supports the standard 800 MHz in-band Plan A1 duplex layout."],
        ),
        TechnicalPlan(
            id="800-A2",
            display_name="800 MHz In-Band Plan A2",
            band_family=BandFamily.BAND_800,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(806.0, 814.0),
            dvrs_tx_window=(851.0, 859.0),
            pair_offset_mhz=45.0,
            pair_direction="tx_above_rx",
            min_separation_from_mobile_tx_mhz=5.0,
            min_separation_from_mobile_rx_mhz=5.0,
            max_dvrs_passband_mhz=3.0,
            active_mobile_tx_window=(811.0, 824.0),
            active_mobile_rx_window=(854.0, 869.0),
            system_700_rx_range=(764.0, 775.0),
            system_700_tx_range=(794.0, 804.0),
            system_800_rx_range=(854.0, 869.0),
            system_800_tx_range=(811.0, 824.0),
            fixed_dvrs_tx_range=(851.0, 859.0),
            fixed_dvrs_rx_range=(806.0, 814.0),
            notes=["Supports the standard 800 MHz in-band Plan A2 duplex layout."],
        ),
        TechnicalPlan(
            id="800-B",
            display_name="800 MHz In-Band Plan B",
            band_family=BandFamily.BAND_800,
            dvrs_mode="duplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(809.0, 824.0),
            dvrs_tx_window=(854.0, 869.0),
            pair_offset_mhz=45.0,
            pair_direction="tx_above_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(806.0, 821.0),
            active_mobile_rx_window=(851.0, 864.0),
            system_700_rx_range=(764.0, 775.0),
            system_700_tx_range=(794.0, 805.0),
            system_800_rx_range=(851.0, 864.0),
            system_800_tx_range=(806.0, 821.0),
            fixed_dvrs_tx_range=(854.0, 869.0),
            fixed_dvrs_rx_range=(809.0, 824.0),
            notes=["Supports the standard 800 MHz in-band Plan B duplex layout."],
        ),
        TechnicalPlan(
            id="800-C",
            display_name="800 MHz In-Band Plan C",
            band_family=BandFamily.BAND_800,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(806.0, 821.0),
            dvrs_tx_window=(851.0, 866.0),
            pair_offset_mhz=45.0,
            pair_direction="tx_above_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(809.0, 824.0),
            active_mobile_rx_window=(854.0, 869.0),
            system_800_rx_range=(854.0, 869.0),
            system_800_tx_range=(809.0, 824.0),
            fixed_dvrs_tx_range=(851.0, 866.0),
            fixed_dvrs_rx_range=(806.0, 821.0),
            notes=["Supports the standard 800 MHz in-band Plan C duplex layout."],
        ),
    ],
}


def classify_regulatory_status(
    country: Country,
    band: BandFamily,
    proposed_tx: tuple[float, float] | None,
    proposed_rx: tuple[float, float] | None,
) -> tuple[RegulatoryStatus, float, list[str]]:
    """Return conservative regulatory classification details."""

    tx_low = proposed_tx[0] if proposed_tx else None
    tx_high = proposed_tx[1] if proposed_tx else None
    rx_low = proposed_rx[0] if proposed_rx else None
    rx_high = proposed_rx[1] if proposed_rx else None

    if tx_low is None or rx_low is None:
        return RegulatoryStatus.NOT_EVALUATED, 0.0, [
            "Regulatory classification skipped because no DVRS proposal could be produced."
        ]

    if country == Country.UNITED_STATES:
        if band == BandFamily.BAND_700:
            if 769.0 <= tx_low <= tx_high <= 775.0 and 799.0 <= rx_low <= rx_high <= 805.0:
                return RegulatoryStatus.LIKELY_LICENSABLE, 0.85, [
                    "Falls within the U.S. 700 MHz public-safety narrowband block."
                ]
            if 851.0 <= tx_low <= tx_high <= 869.0 and 806.0 <= rx_low <= rx_high <= 824.0:
                return RegulatoryStatus.COORDINATION_REQUIRED, 0.7, [
                    "Fits the supported 700/800 interoperability layout, but exact U.S. licensing still depends on the paired 800 MHz channel assignment."
                ]
        if band == BandFamily.BAND_800:
            if 769.0 <= tx_low <= tx_high <= 775.0 and 799.0 <= rx_low <= rx_high <= 805.0:
                return RegulatoryStatus.COORDINATION_REQUIRED, 0.7, [
                    "Fits the supported 700/800 interoperability layout, but exact U.S. licensing still depends on the paired 700 MHz channel assignment."
                ]
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.7, [
                "800 MHz public-safety licensing is plausible but channel-category and border rules still matter."
            ]
    if country == Country.CANADA:
        if band == BandFamily.BAND_700:
            if 768.0 <= tx_low <= tx_high <= 776.0 and 798.0 <= rx_low <= rx_high <= 806.0:
                return RegulatoryStatus.LIKELY_LICENSABLE, 0.85, [
                    "Falls within the Canadian 700 MHz public-safety-capable block."
                ]
            if 851.0 <= tx_low <= tx_high <= 869.0 and 806.0 <= rx_low <= rx_high <= 824.0:
                return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                    "Fits the supported 700/800 interoperability layout, but Canadian assignability still depends on the exact paired 800 MHz channel."
                ]
        if band == BandFamily.BAND_800:
            if 768.0 <= tx_low <= tx_high <= 776.0 and 798.0 <= rx_low <= rx_high <= 806.0:
                return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                    "Fits the supported 700/800 interoperability layout, but Canadian assignability still depends on the exact paired 700 MHz channel."
                ]
            if 821.0 <= rx_low <= rx_high <= 824.0 or 866.0 <= tx_low <= tx_high <= 869.0:
                return RegulatoryStatus.LIKELY_LICENSABLE, 0.75, [
                    "Falls within the Canadian 800 MHz public-safety block."
                ]
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "Canadian 800 MHz assignability depends on the exact sub-allocation and coordination."
            ]
    return RegulatoryStatus.COORDINATION_REQUIRED, 0.4, [
        "No country-specific rule matched; defaulting to coordination required."
    ]

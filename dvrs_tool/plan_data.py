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
            dvrs_rx_window=(799.0, 805.0),
            dvrs_tx_window=(769.0, 775.0),
            pair_offset_mhz=30.0,
            pair_direction="tx_below_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(802.0, 805.0),
            active_mobile_rx_window=(772.0, 775.0),
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
            dvrs_rx_window=(799.0, 805.0),
            dvrs_tx_window=(769.0, 775.0),
            pair_offset_mhz=30.0,
            pair_direction="tx_below_rx",
            min_separation_from_mobile_tx_mhz=3.0,
            min_separation_from_mobile_rx_mhz=3.0,
            max_dvrs_passband_mhz=1.0,
            active_mobile_tx_window=(799.0, 802.0),
            active_mobile_rx_window=(769.0, 772.0),
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
            min_separation_from_mobile_tx_mhz=2.5,
            min_separation_from_mobile_rx_mhz=2.5,
            max_dvrs_passband_mhz=3.0,
            active_mobile_tx_window=(806.0, 819.0),
            active_mobile_rx_window=(851.0, 864.0),
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
            min_separation_from_mobile_tx_mhz=2.5,
            min_separation_from_mobile_rx_mhz=2.5,
            max_dvrs_passband_mhz=3.0,
            active_mobile_tx_window=(811.0, 824.0),
            active_mobile_rx_window=(854.0, 869.0),
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
            fixed_dvrs_tx_range=(851.0, 866.0),
            fixed_dvrs_rx_range=(806.0, 821.0),
            notes=["Supports the standard 800 MHz in-band Plan C duplex layout."],
        ),
    ],
    BandFamily.VHF: [
        TechnicalPlan(
            id="VHF-A",
            display_name="VHF In-Band Plan A",
            band_family=BandFamily.VHF,
            dvrs_mode="duplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase", "Rackmount"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=None,
            pair_offset_mhz=None,
            pair_direction="manual",
            min_separation_from_mobile_tx_mhz=2.0,
            max_dvrs_passband_mhz=0.3,
            requires_mobile_rx_range=True,
            notes=["Ordering guide page 10: valid range 136-174 MHz, DVRS TX/RX split 4.5-5.5 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz."],
        ),
        TechnicalPlan(
            id="VHF-B",
            display_name="VHF In-Band Plan B",
            band_family=BandFamily.VHF,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase", "Rackmount"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=None,
            pair_offset_mhz=None,
            pair_direction="manual",
            min_separation_from_mobile_tx_mhz=2.0,
            max_dvrs_passband_mhz=0.3,
            requires_mobile_rx_range=True,
            notes=["Ordering guide page 10: valid range 136-174 MHz, DVRS TX/RX split 4.5-5.5 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz."],
        ),
        TechnicalPlan(
            id="VHF-D1",
            display_name="VHF Simplex In-Band Plan D1",
            band_family=BandFamily.VHF,
            dvrs_mode="simplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=(136.0, 174.0),
            pair_offset_mhz=0.0,
            pair_direction="simplex",
            min_separation_from_mobile_tx_mhz=2.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 11: DVRS simplex valid range 136-174 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=6 MHz, separation 2-4 MHz."],
        ),
        TechnicalPlan(
            id="VHF-D2",
            display_name="VHF Simplex In-Band Plan D2",
            band_family=BandFamily.VHF,
            dvrs_mode="simplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=(136.0, 174.0),
            pair_offset_mhz=0.0,
            pair_direction="simplex",
            min_separation_from_mobile_tx_mhz=4.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 11: DVRS simplex valid range 136-174 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz, min separation >4 MHz."],
        ),
        TechnicalPlan(
            id="VHF-E1",
            display_name="VHF Simplex In-Band Plan E1",
            band_family=BandFamily.VHF,
            dvrs_mode="simplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=(136.0, 174.0),
            pair_offset_mhz=0.0,
            pair_direction="simplex",
            min_separation_from_mobile_tx_mhz=2.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 11: DVRS simplex valid range 136-174 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=6 MHz, separation 2-4 MHz."],
        ),
        TechnicalPlan(
            id="VHF-E2",
            display_name="VHF Simplex In-Band Plan E2",
            band_family=BandFamily.VHF,
            dvrs_mode="simplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase"],
            dvrs_rx_window=(136.0, 174.0),
            dvrs_tx_window=(136.0, 174.0),
            pair_offset_mhz=0.0,
            pair_direction="simplex",
            min_separation_from_mobile_tx_mhz=4.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 11: DVRS simplex valid range 136-174 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz, min separation >4 MHz."],
        ),
    ],
    BandFamily.UHF_380: [
        *[
            TechnicalPlan(
                id=f"UHF380-{suffix}",
                display_name=f"UHF 380-430 In-Band Plan {suffix}",
                band_family=BandFamily.UHF_380,
                dvrs_mode="duplex",
                placement="above_mobile_tx" if suffix.startswith("A") or suffix == "C" else "below_mobile_tx",
                mount_compatibility=["VehicleMount", "Suitcase", "Rackmount"],
                dvrs_rx_window=(380.0, 430.0),
                dvrs_tx_window=None,
                pair_offset_mhz=5.0,
                pair_direction=(
                    "tx_above_rx"
                    if suffix in {"A1", "A3", "B1", "B3", "C"}
                    else "tx_below_rx"
                ),
                min_separation_from_mobile_tx_mhz=2.0,
                max_dvrs_passband_mhz=0.1 if suffix.startswith("A") or suffix.startswith("B") else 0.3,
                requires_mobile_rx_range=False,
                notes=[
                    "Ordering guide pages 12-14: valid range 380-430 MHz for all windows. "
                    + (
                        "Plans A1/A3 and B1/B3 use TX-5 MHz=RX; plans A2/A4 and B2/B4 use TX+5 MHz=RX; "
                        "plans A1-A4 and B1-B4 use DVRS max passband <=0.1 MHz and MSU max bandwidth <=4 MHz."
                        if suffix.startswith("A") or suffix.startswith("B")
                        else "Plan C uses TX-5 MHz=RX and Plan D uses TX+5 MHz=RX; plans C and D use DVRS max passband <=0.3 MHz and MSU max bandwidth <=12 MHz."
                    )
                ],
            )
            for suffix in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C", "D"]
        ]
    ],
    BandFamily.UHF_450: [
        TechnicalPlan(
            id="UHF450-A",
            display_name="UHF 450-470 In-Band Plan A",
            band_family=BandFamily.UHF_450,
            dvrs_mode="duplex",
            placement="above_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase", "Rackmount"],
            dvrs_rx_window=(450.0, 470.0),
            dvrs_tx_window=(450.0, 470.0),
            pair_offset_mhz=None,
            pair_direction="manual",
            min_separation_from_mobile_tx_mhz=5.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 15: valid range 450-470 MHz, DVRS TX/RX split 4.5-5.5 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz."],
        ),
        TechnicalPlan(
            id="UHF450-B",
            display_name="UHF 450-470 In-Band Plan B",
            band_family=BandFamily.UHF_450,
            dvrs_mode="duplex",
            placement="below_mobile_tx",
            mount_compatibility=["VehicleMount", "Suitcase", "Rackmount"],
            dvrs_rx_window=(450.0, 470.0),
            dvrs_tx_window=(450.0, 470.0),
            pair_offset_mhz=None,
            pair_direction="manual",
            min_separation_from_mobile_tx_mhz=5.0,
            max_dvrs_passband_mhz=0.3,
            notes=["Ordering guide page 15: valid range 450-470 MHz, DVRS TX/RX split 4.5-5.5 MHz, DVRS max passband <=0.3 MHz, MSU max bandwidth <=12 MHz."],
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
        if band == BandFamily.VHF:
            if 173.2375 <= tx_low <= tx_high <= 173.3125 or 173.2375 <= rx_low <= rx_high <= 173.3125:
                return RegulatoryStatus.LIKELY_LICENSABLE, 0.8, [
                    "Aligns with the FCC public-safety mobile repeater channel set cited in the project research."
                ]
            if tx_low < 150.0 or rx_low < 150.0:
                return RegulatoryStatus.LIKELY_NOT_LICENSABLE, 0.8, [
                    "Falls outside the VHF range that is typically public-safety-plausible for non-federal users."
                ]
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "VHF public-safety use is possible, but assignability is channel-specific."
            ]
        if band == BandFamily.UHF_380:
            return RegulatoryStatus.LIKELY_NOT_LICENSABLE, 0.9, [
                "380-430 MHz is generally not a typical non-federal public-safety assignment range in the U.S."
            ]
        if band == BandFamily.UHF_450:
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "450-470 MHz may be assignable for public safety, but not across the entire band."
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
        if band == BandFamily.VHF:
            if tx_low < 148.0 or rx_low < 148.0:
                return RegulatoryStatus.LIKELY_NOT_LICENSABLE, 0.8, [
                    "136-148 MHz is not treated as ordinary public-safety-capable spectrum in this v1 policy."
                ]
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "148-174 MHz may be used for land mobile and public safety, but assignment is coordinated."
            ]
        if band == BandFamily.UHF_380:
            if tx_low < 406.1 or rx_low < 406.1:
                return RegulatoryStatus.LIKELY_NOT_LICENSABLE, 0.8, [
                    "380-406.1 MHz is not treated as ordinary public-safety-capable spectrum in this v1 policy."
                ]
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "406.1-430 MHz may be licensable with coordination in Canada."
            ]
        if band == BandFamily.UHF_450:
            return RegulatoryStatus.COORDINATION_REQUIRED, 0.65, [
                "450-470 MHz may be licensable with coordination in Canada."
            ]

    return RegulatoryStatus.COORDINATION_REQUIRED, 0.4, [
        "No country-specific rule matched; defaulting to coordination required."
    ]

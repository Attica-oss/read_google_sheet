"""Dataset configuration and naming conventions for IPHS operations"""

from enum import StrEnum


class OperationDataset(StrEnum):
    """Class to select google sheet datasets"""

    GATE_IN = "container_gate_in"
    GATE_OUT = "container_gate_out"
    TRANSFER = "transfer"
    SALT_CREWING = "salt_stevedoring"
    SALT = "salt_operation"
    PTI_LOGISTICS = "container_pti_log"
    ELECTRICITY_LOGISTICS = "container_plugin_log"
    PTI = "container_pti"
    WELL_TO_WELL = "well_to_well"
    FORKLIFT = "forklift"
    SHORE_CRANE = "shore_crane"
    REPORT_STATUS = "validation"
    PRICE = "price"
    WASHING_LOGISTICS = "container_cleaning_log"
    WASHING = "container_cleaning"
    CROSS_STUFFING = "cross_stuffing"
    TIPPING_TRUCK = "tipping_truck"
    BY_CATCH_LOGISTICS = "by_catch_transfer_driver"
    SCOW_TRANSFER = "scow_transfer"
    SHIFTING = "container_shifting"
    OPERATIONS_ACTIVITY = "operations_activity"
    COLD_STORE_STUFFING = "cccs_container_stuffing"
    MISCELLANEOUS_SERVICE = "miscellaneous_ops"
    TEMPERATURE = "container_temperature_log"
    COLD_STORE_ACTIVITY = "cccs_activity"
    PALLETS = "pallet_and_liner"
    ELECTRICITY = "electricity"
    NET_LIST = "net_list"
    BY_CATCH_TRANSFER = "by_catch_transfer"
    CUSTOMER = "customer"
    ADDITIONAL_SHIFTING_LOG = "additional_shifting_log"

    def to_lower(self) -> str:
        """Lower case the datasets name"""
        return self.value.lower()

    @classmethod
    def list_all(cls) -> list[str]:
        """List all dataset names"""
        return [dataset.value for dataset in cls]


type ConfigName = str | OperationDataset

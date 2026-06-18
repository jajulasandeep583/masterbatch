import frappe
from frappe.model.document import Document


def _num(v):
    """Tidy numeric display: 18.0 -> '18', 0.10 -> '0.1', 1.30 -> '1.3'."""
    v = v or 0
    if v == int(v):
        return str(int(v))
    return ("%.3f" % v).rstrip("0").rstrip(".")


class QCParameter(Document):
    def before_save(self):
        self.specification = self.build_specification()

    def build_specification(self):
        et = self.evaluation_type or "Range"
        if et == "Text Match":
            return ("= %s" % self.target_text) if self.target_text else ""
        if et == "Minimum":
            return "≥ %s" % _num(self.min_value)
        if et == "Maximum":
            return "≤ %s" % _num(self.max_value)
        return "%s – %s" % (_num(self.min_value), _num(self.max_value))

# -*- coding: utf-8 -*-

import logging
from openerp.exceptions import UserError
from odoo import models, tools, fields, api, _
_logger = logging.getLogger(__name__)


class CompareRecord(models.Model):
    _name = 'compare.record'
    _description = 'Model for comparing records.'

    name = fields.Char("Name", required=True)
    model = fields.Char("Model Name", placeholder="Model Name e.g. res.partner", required=True)
    ignored_fields = fields.Text("Ignored Fields", placeholder="Fields Name e.g. create_date, write_date", help="comma separated fields name", default="create_date, write_date, create_uid, write_uid,")
    record_id_one = fields.Integer("Record ID-1", required=True, pleaceholder="ID", help="Record id-1 for comparison.")
    record_id_two = fields.Integer("Record ID-2", required=True, pleaceholder="ID", help="Record id-2 for comparison.")
    compare_record_line_ids = fields.One2many("compare.record.line", "compare_record_id", "Comparison Table")

    def compare_record(self):
        self.ensure_one()
        if self.compare_record_line_ids:
            self.compare_record_line_ids.unlink()
        temp = []
        search_read_list = []
        if self.model and not (self.model in self.env):
            raise UserError(_("Model %r does not exist!" %self.model))
        ModelRefSudo = self.env[self.model].sudo()
        if self.record_id_one:
            search_read_rec_one = ModelRefSudo.search_read([("id", "=", self.record_id_one)])
            if not search_read_rec_one:
                raise UserError(_("Model %r has no record with id = %r !" %(self.model, self.record_id_one)))
            else:
                search_read_list.append(search_read_rec_one[0])
        else:
            raise UserError(_("Record ID-1 has wrong value %r !" %(self.record_id_one)))
        if self.record_id_two:
            search_read_rec_two = ModelRefSudo.search_read([("id", "=", self.record_id_two)])
            if not search_read_rec_two:
                raise UserError(_("Model %r has no record with id = %r !" %(self.model, self.record_id_two)))
            else:
                search_read_list.append(search_read_rec_two[0])
        else:
            raise UserError(_("Record ID-2 has wrong value %r !" %(self.record_id_two)))
        if len(search_read_list) == 2:
            # If below code get execute means both record exist
            fields_list = search_read_list[0].keys()
            ignored_fields = set((self.ignored_fields + ",id").replace(" ", "").split(","))
            for field in fields_list:
                if field not in ignored_fields:
                    temp.append({
                        "field_name": field,
                        "record_one_value": search_read_list[0].get(field),
                        "record_two_value": search_read_list[1].get(field),
                        "compare_record_id": self.id,
                    })
            self.env["compare.record.line"].create(temp)
        else:
            raise UserError(_("Record not found!!!"))

class CompareRecordLine(models.Model):
    _name = "compare.record.line"
    _description = 'Model for comparing record lines.'
    _rec_name = "compare_record_id"
    _order = "is_both_value_same"

    compare_record_id = fields.Many2one("compare.record", "Compare Record", required=True)
    field_name = fields.Char("Field Name", required=True, help="Technical name of the field.")
    record_one_value = fields.Char("Record1 Value")
    record_two_value = fields.Char("Record2 Value")
    is_both_value_same = fields.Boolean(compute="_compute_is_same_value", string="Value Same?")

    @api.depends("record_one_value", "record_two_value")
    def _compute_is_same_value(self):
        for rec in self:
            rec.is_both_value_same = True if rec.record_one_value == rec.record_two_value else False

    _sql_constraints = [
        ('field_name_unique_per_record', 'unique (field_name, compare_record_id)', 'This field name is already exists for the same record...!')
    ]

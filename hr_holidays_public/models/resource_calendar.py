# Copyright 2017-2018 Tecnativa - Pedro M. Baeza
# Copyright 2018 Brainbean Apps
# Copyright 2020 InitOS Gmbh
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.tools.intervals import Intervals


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _attendance_intervals_batch_exclude_public_holidays(
        self, start_dt, end_dt, intervals, resources
    ):
        employee_id = self.env.context.get("employee_id", False)
        if not employee_id:
            return intervals
        employee = self.env["hr.employee.public"].browse(employee_id)
        # We will use the address of the employee or the partner of the company; the
        # goal is to check only the public holidays for a specific country.
        partner = employee.address_id or employee.company_id.partner_id
        list_by_dates = (
            self.env["calendar.public.holiday"]
            .get_holidays_list(
                start_dt=start_dt.date(),
                end_dt=end_dt.date(),
                partner_id=partner.id,
            )
            .mapped("date")
        )
        for resource in resources:
            interval_resource = intervals[resource.id]
            attendances = []
            for attendance in interval_resource:
                if attendance[0].date() not in list_by_dates:
                    attendances.append(attendance)
            intervals[resource.id] = Intervals(attendances)
        return intervals

    def _attendance_intervals_batch(
        self, start_dt, end_dt, resources_per_tz=None, domain=None
    ):
        # Odoo 20: resources come grouped by timezone (resources_per_tz)
        res = super()._attendance_intervals_batch(
            start_dt, end_dt, resources_per_tz=resources_per_tz, domain=domain
        )
        if self.env.context.get("exclude_public_holidays") and resources_per_tz:
            resources = self.env["resource.resource"].union(*resources_per_tz.values())
            if not resources:
                return res
            # We need to pass the employee_id to the context to be able to filter
            # the public holidays correctly
            employees = resources.employee_id
            if len(employees) == 1:
                self = self.with_context(employee_id=employees.id)
            return self._attendance_intervals_batch_exclude_public_holidays(
                start_dt, end_dt, res, resources
            )
        return res

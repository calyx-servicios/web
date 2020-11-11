##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import re
import logging
_logger = logging.getLogger(__name__)


class Attachment(models.Model):
	_inherit = "ir.attachment"

	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
		res_model = None
		for t in domain:
			if t[0] == 'res_model':
				res_model = t[2]
			if t[0] == 'res_id':
				res_id = t[2]
		res2 = []


		if res_model and res_model in ['crm.lead', 'sale.order', 'purchase.order', 'account.invoice']:
			lead_id, sale_ids, purchase_ids, invoice_ids= [], [], [], []
			if res_model == 'crm.lead':
				sale_ids = self.env['sale.order'].search([('opportunity_id','=',res_id)])
				# for order in purchase_ids:
				# 		invoice_ids += order.invoice_ids
				for sale in sale_ids:
					purchase_ids = self.env['sale.order'].browse(sale.id).purchase_ids
					for order in purchase_ids:
						invoice_ids += order.invoice_ids
					invoice_ids += sale.mapped('invoice_ids')
					
			elif res_model == 'sale.order':
				lead_id = self.env['sale.order'].browse(res_id).opportunity_id.id
				purchase_ids = self.env['sale.order'].browse(res_id).purchase_ids
				invoice_ids += self.env['sale.order'].browse(res_id).mapped('invoice_ids')
				for order in purchase_ids:
					invoice_ids += order.invoice_ids
			elif res_model == 'purchase.order':
				sale_ids = self.env['purchase.order'].browse(res_id).sale_ids
				for sale in sale_ids:
					lead_id = self.env['sale.order'].browse(sale.id).opportunity_id.id
					invoice_ids += sale.mapped('invoice_ids')
				invoice_ids += self.env['purchase.order'].browse(res_id).invoice_ids
			elif res_model == 'account.invoice':
				line_ids = self.env['account.invoice'].browse(res_id).invoice_line_ids
				for line in line_ids:
					if self.env['account.invoice'].browse(res_id).type in ['out_invoice', 'out_refund']: 
						for sale_line in line.sale_line_ids:
							sale_ids.append(sale_line.order_id)
							purchase_ids += sale_line.order_id.purchase_ids
							lead_id = self.env['sale.order'].browse(sale_line.order_id.id).opportunity_id.id
							for order in purchase_ids:
								invoice_ids += order.invoice_ids
					if self.env['account.invoice'].browse(res_id).type in ['in_invoice', 'in_refund']:
						if line.purchase_line_id:
							purchase_ids.append(line.purchase_line_id)
							sale_ids += line.purchase_line_id.order_id.sale_ids
							for sale in sale_ids:
								invoice_ids += sale.mapped('invoice_ids')
								lead_id = self.env['sale.order'].browse(sale.id).opportunity_id.id

			for order in sale_ids:
				domain2 =[['res_model', '=', 'sale.order'], ['res_id', '=', int(order.id)], ['type', 'in', ['binary', 'url']]]
				res2 += super(Attachment, self).search_read(domain2, fields)
			for order in purchase_ids:
				domain2 =[['res_model', '=', 'purchase.order'], ['res_id', '=', int(order.id)], ['type', 'in', ['binary', 'url']]]
				res2 += super(Attachment, self).search_read(domain2, fields)
			if lead_id:
				domain2 =[['res_model', '=', 'crm.lead'], ['res_id', '=', int(lead_id)], ['type', 'in', ['binary', 'url']]]
				res2 += super(Attachment, self).search_read(domain2, fields)
			for invoice in invoice_ids:
				domain2 =[['res_model', '=', 'account.invoice'], ['res_id', '=', invoice.id], ['type', 'in', ['binary', 'url']]]
				res2 += super(Attachment, self).search_read(domain2, fields)


		res = super(Attachment, self).search_read(domain, fields)
		return res+res2
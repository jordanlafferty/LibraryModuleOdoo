from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BookCategory(models.Model):
    _name = 'library.book.category'

    _parent_store = True
    _parent_name = "parent_id"  # optional if field is 'parent_id'

    name = fields.Char('Category')
    description = fields.Text('Description')
    parent_id = fields.Many2one( # a child can only have one parent
        'library.book.category',
        string='Parent Category',
        ondelete='restrict',
        index=True #used to find child record faster
    )
    child_ids = fields.One2many( # a parent can have multiple children
        'library.book.category', 'parent_id',
        string='Child Categories')
    parent_path = fields.Char(index=True)


    # makes sure there is not cyclic dependencies
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error! You cannot create recursive categories.')


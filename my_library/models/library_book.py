import datetime
import logging
from datetime import timedelta


import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

logger = logging.getLogger(__name__)
_logger = logging.getLogger(__name__)

class BaseArchive(models.AbstractModel):
    _name='base.archive'
    _description = 'Abstract Archive'

    active=fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active= not record.active

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    _order = 'date_release desc, name'

    name = fields.Char('Title', required=True, index=True)
    short_name = fields.Char('Short Title',translate=True, index=True)
    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', 'Not Available'),
         ('available', 'Available'),
         ('lost', 'Lost'),
         ('borrowed', 'Borrowed'),
         ('damaged', 'Damaged')],
        'State', default="draft")
    description = fields.Html('Description', sanitize=True, strip_style=False) #if strip_style was true it would rewmove all style elements
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated', copy=False)
    pages = fields.Integer('Number of Pages',
        groups='base.group_user',
        states={'lost': [('readonly', True)]},
        help='Total book page count', company_dependent=False)
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  # Optional precision (total, decimals)
    )
    curr_renter =fields.Many2one('res.partner', string='Current Renter', readonly=True)
    prev_renter =fields.Many2one('res.partner', string='Previous Renter',readonly=True)
    checkout_date=fields.Date('Checkout Date', readonly=True)
    ratingbook= fields.One2many('library.book.rating', 'book_id', string='Book Ratings', readonly=True)
    book_avg = fields.Float(string='Rating', digits='Book Price')


    isbn = fields.Char('ISBN')
    manager_remarks = fields.Text('Manager Remarks')
    author_ids = fields.Many2many('res.partner', string='Authors') #each author can have many books and each book can only have many authors
    old_edition = fields.Many2one('library.book', string='Old Edition')
    cost_price = fields.Float('Book Cost', digits='Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price') 

    publisher_id = fields.Many2one('res.partner', string='Publisher', #each book can only have one publisher
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )
    
    publisher_city = fields.Char('Publisher City', related='publisher_id.city', readonly=True)

    category_id = fields.Many2one('library.book.category')
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age', inverse='_inverse_age', search='_search_age',
        store=False,
        compute_sudo=True,
    )

    ref_doc_id = fields.Reference(selection='_referencable_models', string='Reference Document')

    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([('field_id.name', '=', 'message_ids')])
        return [(x.model, x.name) for x in models]

    @api.depends('date_release') # decorator needs to know what this depends on and is used to detect when to recalculate
    def _compute_age(self):
        today = fields.Date.today()
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

    # This reverse method of _compute_age. Used to make age_days field editable
    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

    # This used to enable search on copute fields
    def _search_age(self, operator, value):
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]

    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        for record in self:
            rec_name = "%s (%s)" % (record.name, record.date_release)
            result.append((record.id, rec_name))
        return result


    # constraint enforced at the database level
    # book title has top be unique and there has to be at least 1 page
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Book title must be unique.'),
        ('positive_page', 'CHECK(pages>0)', 'No of pages must be positive')
    ]

    # date should be checked everytime the field changes and it can't be in the future
    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')


    # defines the transitions that are allowed
    @api.model
    def is_allowed_for_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available'),
                   ('damaged', 'available'),
                   ('damaged', 'lost'),
                   ('available', 'damaged'),
                   ('borrowed', 'damaged'),
                   ('damaged', 'draft')]
        return(old_state, new_state) in allowed

    # changes the state of the group if it is allowed
    def change_state(self,new_state):
        for book in self:
            if book.is_allowed_for_transition(book.state, new_state):
                book.state = new_state
            else:
                msg =_('Moving from %s to %s is not allowed') %(book.state, new_state)
                raise UserError(msg)
    
    def return_book(self):
        # only if the state is borrowed
        #change the state to available and reset curr renter, previous renter and checkout date
        
        self.change_state('available')
        #self.adjust_rents()
        self.checkout_date = None
        self.prev_renter = self.curr_renter
        self.curr_renter = None
    
    def create_invoice(self, invoice_amount, invoice_item, invoice_type):

        move = self.env['account.move'].create({
            'state': 'draft',
            'move_type': invoice_type,
            'partner_id': self.curr_renter.id,
            'invoice_date': fields.Date.today(),

            'invoice_line_ids': [
                (0, None, {
                    'name': '{} - {}'.format(invoice_item, self.name),
                    'price_unit': invoice_amount
                })
            ]
        })
        return move

    def make_available(self):
        if self.state == 'lost':
            self.create_invoice(10, 'Refund Amount', 'out_refund')
        self.change_state('available') #connected to a button in view

    def make_borrowed(self):
        self.change_state('borrowed') #connected to a button in view
        self.checkout_date = fields.Date.today()
        

    def make_lost(self):
        self.create_invoice(5, 'Damaged Book Fee', 'out_invoice')
        self.change_state('lost') #connected to a button in view

    def make_damaged(self):
        self.create_invoice(5, 'Damaged Book Fee', 'out_invoice')
        self.change_state('damaged')

    def make_unavailable(self):
        self.change_state('draft')
    

    
    def post_to_webservice(self,data):
        try:
            req= requests.post('http://my-test-service.com',data=data, timeout=10)
            content =req.json()
        except IOError:
            error_msg=_("something went wrong during data submission")
            raise UserError(error_msg)
        return content
    
    
    def log_all_library_members(self):
        library_member_model = self.env['library.member']  # This is an empty recordset of model library.member
        all_members = library_member_model.search([])
        print("ALL MEMBERS:", all_members)
        return True

    def create_categories(self):
        categ1 = {
            'name':'Child category 1',
            'description':'Description for child 1'
        }
        categ2 = {
            'name':'Child category 2',
            'description':'Description for child 2'
        }
        parent_category_val = {
            'name': 'Parent category',
            'description':'Description for parent category',
            'child_ids': [
                (0, 0, categ1),
                (0, 0, categ2),
            ]
        }
        # Total 3 records (1 parent and 2 child) will be craeted in library.book.category model
        record = self.env['library.book.category'].create(parent_category_val)
        return True

    def change_release_date(self):
        self.ensure_one()
        self.date_release = fields.Date.today() # one way of updating records

        #would update multiple fields
        #self.update({
            #'date_release':fields.Datetime.now()
            #'another_field': 'value'
        #})

    
        

    def set_curr_renter(self, renter):
        self.curr_renter = renter

    


class LibraryMember(models.Model):

    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}
    _description = "Library member"

    partner_id = fields.Many2one('res.partner', ondelete='cascade')
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')
    
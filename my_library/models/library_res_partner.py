import logging
from odoo import fields, models, api
from odoo.exceptions import UserError


class LibraryResPartner(models.Model):
    _inherit = 'res.partner'

    published_book_ids = fields.One2many('library.book', 'publisher_id', string='Published Books')
    curr_renter=fields.One2many('library.book','curr_renter', string="Current Renter")
    prev_renter=fields.One2many('library.book','prev_renter', string="Previous Renter")
    authored_book_ids = fields.Many2many(
        'library.book',
        string='Authored Books',
        # relation='library_book_res_partner_rel'  # optional
    )
    
    count_books = fields.Integer('Number of Authored Books', compute='_compute_count_books')

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)


    review_book_id = fields.One2many('library.book.rating','borrower_id',string='Reviewed Books',store=True)
    
    borrower_id = fields.One2many('library.book','curr_renter', string='Borrowed Book')

    borrower_ids = fields.One2many('library.book.rent','borrower_id',string='Borrowed Books')



    # Book rent history
    book_history_count = fields.Integer(string='Records Count', compute='_compute_history_count', store=False,computer_sudo=True)

    @api.depends('borrower_ids')
    def _compute_history_count(self):
        for partner in self:
            history_model = self.env['library.book.rent']
            history_ids = history_model.search([('borrower_id.id', '=', self.id)])
            if history_ids:
                partner.book_history_count = len(history_ids)
            else:
                partner.book_history_count = 0
    
    def books_history(self):
        for partner in self:
            history_model = self.env['library.book.rent']
            history_ids = history_model.search([
                ('borrower_id.id', '=', self.id)
            ])

            action = self.env.ref('my_library.library_book_rent_action').read()[0]
            action['context'] = {}

            if len(history_ids) == 0:
                raise UserError('The user has not borrowed any books in the past.')

            if len(history_ids) == 1:
                action['views'] = [
                    (self.env.ref('my_library.library_book_rent_view_form').id, 'form')
                ]
                action['res_id'] = history_ids[0].id
            
            else:
                action['domain'] = [('borrower_id.id', '=', self.id)]

            return action
  
    # Books currently being rented
    book_borrowed_count = fields.Integer(string='Books Currently Rented',compute='_compute_rented_count',store=False,computer_sudo=True)

    def _compute_rented_count(self):
        for partner in self:
            books_model = self.env['library.book']
            book_ids = books_model.search([
                ('curr_renter.id', '=', self.id)
            ])
            if book_ids:
                partner.book_borrowed_count = len(book_ids)
            else:
                partner.book_borrowed_count = 0
            
    def books_checked_out(self):
        for partner in self:
            books_model = self.env['library.book']
            book_ids = books_model.search([
                ('curr_renter.id', '=', self.id)
            ])

            action = self.env.ref('my_library.library_book_action').read()[0]
            action['context'] = {}
            
            if len(book_ids) == 0:
                raise UserError('The user has not borrowed any books.')

            if len(book_ids) == 1:
                action['views'] = [
                    (self.env.ref('my_library.library_book_view_form').id, 'form')
                ]
                action['res_id'] = book_ids[0].id
                
            else:
                action['domain'] = [('curr_renter.id', '=', self.id)]
                
            return action

    # Book Ratings
    book_reviewed_count = fields.Integer(string='Reviewed Count',compute='_compute_reviewed_count',store=False,computer_sudo=True)
    
    def _compute_reviewed_count(self):
        for partner in self:
            ratings_model = self.env['library.book.rating']
            rating_ids = ratings_model.search([
                ('borrower_id.id', '=', self.id)
            ])

            logging.info(rating_ids)

            if rating_ids:
                partner.book_reviewed_count = len(rating_ids)
            else:
                partner.book_reviewed_count = 0

    # Method
    def books_reviewed(self):
        for partner in self:
            logging.info("Here is the log: {}".format(partner.book_reviewed_count))
            ratings_model = self.env['library.book.rating']
            rating_ids = ratings_model.search([
                ('borrower_id.id', '=', self.id)
            ])

            action = self.env.ref('my_library.library_book_rating_action').read()[0]
            action['context'] = {}

            if len(rating_ids) == 0:
                raise UserError('The user has not reviewed any books.')

            if len(rating_ids) == 1:
                action['views'] = [
                    (self.env.ref('my_library.library_book_rating_view_form').id, 'form')
                ]
                action['res_id'] = rating_ids[0].id
            
            else:
                action['domain'] = [('borrower_id.id', '=', self.id)]
            
            return action
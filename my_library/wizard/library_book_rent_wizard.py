# -*- coding: utf-8 -*-
from odoo import api, models, fields


class LibraryRentWizard(models.TransientModel):
    _name = 'library.rent.wizard'

    borrower_id = fields.Many2one('res.partner', string='Borrower')
    book_ids = fields.Many2one('library.book', string='Books')

    def add_book_rents(self):
        rentModel = self.env['library.book.rent']
        for wiz in self:
            for book in wiz.book_ids:
                rentModel.create({
                    'borrower_id': wiz.borrower_id.id,
                    'book_id': book.id
                })
                
    @api.model
    def create(self, vals):
        # book_rec = self.env['library.book'].browse(vals['book_ids'])  # returns record set from for given id
        # book_rec.make_borrowed()

        # book_rec2 = self.env['library.book'].browse(vals['borrower_id'])  # returns record set from for given id
        # book_rec2.add_rentername(self.borrower_id)
        # self.renter_name = self.borrower_id

        # renter_name = self.env['library.rent.wizard'].search([
        #     ('borrower_id', '=', vals['borrower_id'])
        # ])
        bookModel = self.env['library.book']
        bookval = bookModel.search([
            ('id', '=', vals['book_ids'])
        ])
        # logging.info(renter_name)
        bookval.curr_renter = vals['borrower_id']
        bookModel.write(bookval)
        #bookModel.change_state('borrowed')
        book_rec = self.env['library.book'].browse(vals['book_ids'])  # returns record set from for given id
        #book_rec.make_borrowed()

        # test = bookModel.search([
        #     ('renter_name', '=', vals['borrower_id'])
        # ])
        # logging.info(renter_name)
        # test.renter_name = renter_name
        # bookModel.write(test)

        return super(LibraryRentWizard, self).create(vals)
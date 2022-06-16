from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryBookRating(models.Model):
    _name ='library.book.rating'

    borrower_id = fields.Many2one('res.partner', 'Reviewer', required=True)
    book_id = fields.Many2one('library.book', 'Book', required=True)

    rating = fields.Selection([('1', 1),
            ('1.5', 1.5),
            ('2', 2),
            ('2.5', 2.5),
            ('3', 3),
            ('3.5', 3.5),
            ('4', 4),
            ('4.5', 4.5),
            ('5', 5)],
            )

    @api.model
    def create(self, val):
        #self.add_rating()
        ratings = self.env['library.book.rating'].search([('book_id', '=', val['book_id'])])
        bookModel = self.env['library.book']

        sum_ratings = sum(float(book.rating) for book in ratings) + float(val['rating'])
        book_search = bookModel.search([
            ('id', '=', val['book_id'])
        ])[0]
        book_search.book_avg = str(sum_ratings / (len(ratings)+1))
        bookModel.write(book_search)
        # book_rec = self.env['library.book'].browse(vals['book_id'])  # returns record set from for given id
        # book_rec.new_rating = float(self.rating)
        # book_rec.compute_rating()
        return super(LibraryBookRating, self).create(val)

    # def create_action_rating(self):
    #     return{
    #         'type': 'ir.action.act_window',
    #         'name': 'Reviews'}


    def add_rating(self):
        self.rating_list.append(self.rating)
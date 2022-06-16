from odoo import api, models, fields


class BookReviewWizard(models.TransientModel):
    _name = 'book.review.wizard'

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
        return super(BookReviewWizard, self).create(val)

    def add_book_reviews(self):
        pass


    # @api.depends('borrower_id')
    # def onchange_member(self):
    #     reviewModel = self.env['book.review.wizard']
    #     book_rec = self.env['library.book']  # returns record set from for given id
    #     book_rec.add_ratings('rating_id')
    #     books_on_rent = reviewModel.search(
    #         [('state', '=', 'returned'),
    #          ('borrower_id', '=', self.borrower_id.id)]
    #     )
    #     self.book_ids = books_on_rent.mapped('book_id')
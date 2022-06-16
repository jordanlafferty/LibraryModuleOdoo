from odoo import models, fields, api



class LibraryBookCopy(models.Model):
    _inherit ="library.book"
    
    _name = 'library.book.copy'
    _description = "Library Book's Copy"

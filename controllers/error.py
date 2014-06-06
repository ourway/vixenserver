
def index():
    #~ return request.vars.code
    ticket=request.vars.ticket
    ticket_url = '#'
    if ticket:
        
        ticket_url = '/admin/default/ticket/%s' % ticket

    return dict(ticket=ticket, ticket_url =ticket_url , code=request.vars.code)

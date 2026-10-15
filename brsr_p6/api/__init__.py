"""The data service behind the React page (web/): serves each report's Dashboard data as JSON, and the built React app itself.

It only READS what the other layers already produce (it never recalculates or corrects a number), so the React page and the chat assistant
see exactly the figures, sentences, units and warnings that the HTML pages show.
"""

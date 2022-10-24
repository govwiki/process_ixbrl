import sys

import pandas as pd

from ixbrl import XbrliDocument

# Taxonomy V1.0 Files
# Use one of these as the command line argument when calling parse_acfr_ixbrl.py
# ixbrl_files = ['https://xbrlus.github.io/acfr/samples/67/Ogemaw-20190930.htm', \
# 'https://xbrlus.github.io/acfr/samples/69/20190331-PineRiverTwnshp.htm', \
# 'https://xbrlus.github.io/acfr/samples/68/SOUTHHAVEN.htm']

context = pd.DataFrame(
    columns=['contextref', 'dimension1', 'memberstring1', 'dimension2', 'memberstring2', 'instant', 'StartDate',
             'EndDate'])
ixdata = pd.DataFrame(columns=['document', 'itemname', 'contextref', 'value'])


def display(text):
    ''' Returns a display-friendly version of the text. '''
    return text.replace('acfr:', '').replace('Axis', '').replace('Member', '')


fileloc = sys.argv[1]

ixbrl_doc = XbrliDocument(path=fileloc)
for context_obj in ixbrl_doc.contexts.values():
    dimension1 = dimension2 = dimension3 = memberstring1 = memberstring2 = memberstring3 = ''
    for index, explicitmember in enumerate(context_obj.explicit_members.values()):
        if index == 0:
            dimension1 = display(explicitmember.dimension)
            memberstring1 = display(explicitmember.string)
        if index == 1:
            dimension2 = display(explicitmember.dimension)
            memberstring2 = display(explicitmember.string)
        if index == 2:
            dimension3 = display(explicitmember.dimension)
            memberstring3 = display(explicitmember.string)
    tdimension1 = tdimension2 = tdimension3 = tmemberstring1 = tmemberstring2 = tmemberstring3 = ''
    for index, typedmember in enumerate(context_obj.typed_members.values()):
        if index == 0:
            tdimension1 = display(typedmember.dimension)
            tmemberstring1 = display(typedmember.string)
        if index == 1:
            tdimension2 = display(typedmember.dimension)
            tmemberstring2 = display(typedmember.string)
        if index == 2:
            tdimension3 = display(typedmember.dimension)
            tmemberstring3 = display(typedmember.string)
    context = context.append({'contextref': context_obj.id,
                              'dimension1': dimension1,
                              'memberstring1': memberstring1,
                              'dimension2': dimension2,
                              'memberstring2': memberstring2,
                              'dimension3': dimension3,
                              'memberstring3': memberstring3,
                              'tdimension1': tdimension1,
                              'tmemberstring1': tmemberstring1,
                              'tdimension2': tdimension2,
                              'tmemberstring2': tmemberstring2,
                              'tdimension3': tdimension3,
                              'tmemberstring3': tmemberstring3,
                              'instant': context_obj.instant,
                              'StartDate': context_obj.start_date,
                              'EndDate': context_obj.end_date}, ignore_index=True)

for ix_element in ixbrl_doc.ix_elements:
    if ix_element.tag.name.startswith('ix:non'):
        ixdata = ixdata.append({'document': fileloc[41:],  # Replace with NameOfGovernment When Available
                                'itemname': display(ix_element.name),
                                'contextref': ix_element.contextref,
                                'value': ix_element.string}, ignore_index=True)

# context.to_csv('context.csv', index=False)
# ixdata.to_csv('ixdata.csv', index=False)
# taxonomy_extract = pd.read_csv('TaxonomyExtract.csv', encoding='windows-1252')
all_statements = pd.read_csv('AllStatements.csv', encoding='windows-1252')
output = ixdata.merge(context, on='contextref').merge(all_statements, on='itemname').sort_values(
    by=['document', 'itemname'])
output.drop_duplicates(keep='first', inplace=True)

# delete duplicate linkages between government-wide and proprietary fund concepts
output["StatementAndMember1"] = output["Statement"] + "|" + output["memberstring1"]
# output.set_index('StatementAndMember1', inplace=True)
# output.to_csv('output.csv', index=False)

output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|ProprietaryFunds']
output = output.loc[output['StatementAndMember1'] != 'Statement of Net Position|']
output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|ProprietaryFunds']
output = output.loc[output['StatementAndMember1'] != 'Statement of Activities|']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|GovernmentalActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|BusinessTypeActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|PrimaryGovernmentActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Net Position|ComponentUnitDiscretelyPresented']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|GovernmentalActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|BusinessTypeActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|PrimaryGovernmentActivities']
output = output.loc[
    output['StatementAndMember1'] != 'Proprietary Funds Revenues Expenses|ComponentUnitDiscretelyPresented']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|GovernmentalActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|BusinessTypeActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|PrimaryGovernmentActivities']
output = output.loc[output['StatementAndMember1'] != 'Proprietary Funds Cash Flows|ComponentUnitDiscretelyPresented']

output.to_csv('output.csv', index=False,
              columns=['document', 'Statement', 'itemname', 'value', 'memberstring1', 'instant', 'StartDate',
                       'EndDate'])

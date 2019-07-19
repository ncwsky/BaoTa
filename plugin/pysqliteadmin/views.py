#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# editor: mufei(ypdh@qq.com tel:15712150708)
'''
牧飞 _ __ ___   ___   ___  / _| ___(_)
| '_ ` _ \ / _ \ / _ \| |_ / _ \ |
| | | | | | (_) | (_) |  _|  __/ |
|_| |_| |_|\___/ \___/|_|  \___|_|
'''
#+--------------------------------------------------------------------
#|   宝塔第三方应用开发 pysqliteadmin
#+--------------------------------------------------------------------
import sys,os,json,re,datetime,math,urllib,optparse,operator,sqlite3
from jinja2 import Template,Markup, Environment, PackageLoader, FileSystemLoader
from collections import namedtuple, OrderedDict
from functools import wraps
#import public

from flask import render_template, request,redirect, url_for as _url_for, flash, escape, make_response
basedir = os.path.abspath(os.path.dirname(__file__))
prefix="/pysqliteadmin"

from BTPanel import app,session
from pysqliteadmin_config import *
from peewee import *
from peewee import IndexMetadata,sqlite3
from playhouse.migrate import migrate





__all__ = ['scan_sqlite3']

if sys.version_info[0] == 3:
    binary_types = (bytes, bytearray)
    decode_handler = 'backslashreplace'
    numeric = (int, float)
    unicode_type = str
    from io import StringIO
else:
    binary_types = (buffer, bytes, bytearray)
    decode_handler = 'replace'
    numeric = (int, long, float)
    unicode_type = unicode
    from StringIO import StringIO
    

try:
    from peewee import __version__
    peewee_version = tuple([int(p) for p in __version__.split('.')])
except ImportError:
    raise RuntimeError('Unable to import peewee module. Install by running '
                       'pip install peewee')
else:
    if peewee_version <= (3, 0, 0):
        raise RuntimeError('Peewee >= 3.0.0 is required. Found version %s. '
                           'Please update by running pip install --update '
                           'peewee' % __version__)


try:
    from pygments import formatters, highlight, lexers
except ImportError:
    import warnings
    warnings.warn('pygments library not found.', ImportWarning)
    syntax_highlight = lambda data: '<pre>%s</pre>' % data
else:
    def syntax_highlight(data):
        if not data:
            return ''
        lexer = lexers.get_lexer_by_name('sql')
        formatter = formatters.HtmlFormatter(linenos=False)
        return highlight(data, lexer, formatter)


#@app.template_filter('format_index')
def format_index(index_sql):
    split_regex = re.compile(r'\bon\b', re.I)
    if not split_regex.search(index_sql):
        return index_sql
    create, definition = split_regex.split(index_sql)
    return '\nON '.join((create.strip(), definition.strip()))
#@app.template_filter('value_filter')
def value_filter(value, max_length=50):
    if isinstance(value, numeric):
        return value
    if isinstance(value, binary_types):
        if not isinstance(value, (bytes, bytearray)):
            value = bytes(value)  # Handle `buffer` type.
        value = value.decode('utf-8', decode_handler)
    if isinstance(value, unicode_type):
        value = escape(value)
        if len(value) > max_length:
            return ('<span class="truncated">%s</span> '
                    '<span class="full" style="display:none;">%s</span>'
                    '<a class="toggle-value" href="#">...</a>') % (
                        value[:max_length],
                        value)
    return value
column_re = re.compile('(.+?)\((.+)\)', re.S)
column_split_re = re.compile(r'(?:[^,(]|\([^)]*\))+')
def _format_create_table(sql):
    create_table, column_list = column_re.search(sql).groups()
    columns = ['  %s' % column.strip()
               for column in column_split_re.findall(column_list)
               if column.strip()]
    return '%s (\n%s\n)' % (
        create_table,
        ',\n'.join(columns))
#@app.template_filter()
def format_create_table(sql):
    try:
        return _format_create_table(sql)
    except:
        return sql
#@app.template_filter('highlight')
def highlight_filter(data):
    return Markup(syntax_highlight(data))
filter_dict = {'highlight':highlight_filter,
               'value_filter':value_filter,
               'format_index':format_index,
               'format_create_table':format_create_table
               }

def get_flashed_messages(*args,**awgs):
    #session = request.session
    if '_flashes' in session:
        flashes = session.pop('_flashes')
    else:
        flashes = []
    return flashes

def url_for(method, *args,**awgs):
    if method=='static':
        return '/pysqliteadmin/static/'+awgs.get('filename', '')
    
    d = globals()
    if method not in d:
        method = 'pysqliteadmin_'+method

    try:
        rs = _url_for(method, *args,**awgs)
    except:
        raise
    return rs


def get_query_images():
    accum = []
    #image_dir = os.path.join(app.static_folder, 'img')
    image_dir = os.path.join(basedir, 'static', 'img')
    if not os.path.exists(image_dir):
        return accum
    for filename in sorted(os.listdir(image_dir)):
        basename = os.path.splitext(os.path.basename(filename))[0]
        parts = basename.split('-')
        accum.append((parts, 'img/' + filename))
    return accum


def render_template(template_name_or_list, **context):
    #env = Environment(loader=PackageLoader('plugin', 'pysqliteadmin', 'templates'))
    env = Environment(loader=FileSystemLoader(os.path.join(basedir, 'templates')))
    for name, f in filter_dict.items(): env.filters[name] = f    
    tpl = env.get_template(template_name_or_list)
    context.update({'request':request,
                    'url_for':url_for,
                    'now': datetime.datetime.now(),
                    'get_flashed_messages':get_flashed_messages,
                    'session': session,

                    'dataset':dataSetCache.dataset
                    })
    html =  tpl.render(context)
    return html
        
    

def require_table(fn):
    @wraps(fn)
    def inner(table, *args, **kwargs):
        if 'pysqliteadmin-db-id' not in session:
            return redirect('/soft')
        if table not in dataSetCache.dataset.tables:
            abort(404)
        return fn(table, *args, **kwargs)
    return inner

###############################################################
@app.route(prefix+'/home/', methods=['GET','POST'])
@app.route(prefix+'/index/', methods=['GET','POST'])
def pysqliteadmin_index():
    if 'pysqliteadmin-db-id' not in session: return redirect('/soft')
    return render_template('index.html', sqlite=sqlite3)
    


@app.route(prefix+'/create-table/', methods=['POST']) #
def pysqliteadmin_table_create():
    if 'pysqliteadmin-db-id' not in session: return redirect('/soft')
    
    table = (request.form.get('table_name') or '').strip()
    if not table:
        flash('Table name is required.', 'danger')
        return redirect(request.form.get('redirect') or url_for('index'))

    dataSetCache.dataset[table]
    return redirect(url_for('table_import', table=table))

@app.route(prefix+'/<table>/', methods=['GET','POST'])
@require_table
def pysqliteadmin_table_structure(table):
    ds_table = dataSetCache.dataset[table]
    model_class = ds_table.model_class

    dataset = dataSetCache.dataset
    table_sql = dataset.query(
        'SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type = ?',
        [table, 'table']).fetchone()[0]

    return render_template(
        'table_structure.html',
        columns=dataset.get_columns(table),
        ds_table=ds_table,
        foreign_keys=dataset.get_foreign_keys(table),
        indexes=dataset.get_indexes(table),
        model_class=model_class,
        table=table,
        table_sql=table_sql,
        triggers=dataset.get_triggers(table))



def get_request_data():
    if request.method == 'POST':
        return request.form
    return request.args

@app.route(prefix+'/<table>/add-column/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_add_column(table):
    column_mapping = OrderedDict((
        ('VARCHAR', CharField),
        ('TEXT', TextField),
        ('INTEGER', IntegerField),
        ('REAL', FloatField),
        ('BOOL', BooleanField),
        ('BLOB', BlobField),
        ('DATETIME', DateTimeField),
        ('DATE', DateField),
        ('TIME', TimeField),
        ('DECIMAL', DecimalField)))

    request_data = get_request_data()
    col_type = request_data.get('type')
    name = request_data.get('name', '')
    dataset = dataSetCache.dataset
    if request.method == 'POST':
        if name and col_type in column_mapping:
            migrate(
                migrator.add_column(
                    table,
                    name,
                    column_mapping[col_type](null=True)))
            flash('Column "%s" was added successfully!' % name, 'success')
            dataset.update_cache(table)
            return redirect(url_for('table_structure', table=table))
        else:
            flash('Name and column type are required.', 'danger')

    return render_template(
        'add_column.html',
        col_type=col_type,
        column_mapping=column_mapping,
        name=name,
        table=table)

@app.route(prefix+'/<table>/drop-column/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_drop_column(table):
    request_data = get_request_data()
    name = request_data.get('name', '')
    dataset = dataSetCache.dataset
    columns = dataset.get_columns(table)
    column_names = [column.name for column in columns]

    if request.method == 'POST':
        if name in column_names:
            migrate(migrator.drop_column(table, name))
            flash('Column "%s" was dropped successfully!' % name, 'success')
            dataset.update_cache(table)
            return redirect(url_for('table_structure', table=table))
        else:
            flash('Name is required.', 'danger')

    return render_template(
        'drop_column.html',
        columns=columns,
        column_names=column_names,
        name=name,
        table=table)

@app.route(prefix+'/<table>/rename-column/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_rename_column(table):
    request_data = get_request_data()
    rename = request_data.get('rename', '')
    rename_to = request_data.get('rename_to', '')
    dataset = dataSetCache.dataset
    columns = dataset.get_columns(table)
    column_names = [column.name for column in columns]

    if request.method == 'POST':
        if (rename in column_names) and (rename_to not in column_names):
            migrate(migrator.rename_column(table, rename, rename_to))
            flash('Column "%s" was renamed successfully!' % rename, 'success')
            dataset.update_cache(table)
            return redirect(url_for('table_structure', table=table))
        else:
            flash('Column name is required and cannot conflict with an '
                  'existing column\'s name.', 'danger')

    return render_template(
        'rename_column.html',
        columns=columns,
        column_names=column_names,
        rename=rename,
        rename_to=rename_to,
        table=table)

@app.route(prefix+'/<table>/add-index/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_add_index(table):
    request_data = get_request_data()
    indexed_columns = request_data.getlist('indexed_columns')
    unique = bool(request_data.get('unique'))
    dataset = dataSetCache.dataset
    columns = dataset.get_columns(table)

    if request.method == 'POST':
        if indexed_columns:
            migrate(
                migrator.add_index(
                    table,
                    indexed_columns,
                    unique))
            flash('Index created successfully.', 'success')
            return redirect(url_for('table_structure', table=table))
        else:
            flash('One or more columns must be selected.', 'danger')

    return render_template(
        'add_index.html',
        columns=columns,
        indexed_columns=indexed_columns,
        table=table,
        unique=unique)

@app.route(prefix+'/<table>/drop-index/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_drop_index(table):
    request_data = get_request_data()
    name = request_data.get('name', '')
    dataset = dataSetCache.dataset
    indexes = dataset.get_indexes(table)
    index_names = [index.name for index in indexes]

    if request.method == 'POST':
        if name in index_names:
            migrate(migrator.drop_index(table, name))
            flash('Index "%s" was dropped successfully!' % name, 'success')
            return redirect(url_for('table_structure', table=table))
        else:
            flash('Index name is required.', 'danger')

    return render_template(
        'drop_index.html',
        indexes=indexes,
        index_names=index_names,
        name=name,
        table=table)

@app.route(prefix+'/<table>/drop-trigger/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_drop_trigger(table):
    request_data = get_request_data()
    name = request_data.get('name', '')
    dataset = dataSetCache.dataset
    triggers = dataset.get_triggers(table)
    trigger_names = [trigger.name for trigger in triggers]

    if request.method == 'POST':
        if name in trigger_names:
            dataset.query('DROP TRIGGER "%s";' % name)
            flash('Trigger "%s" was dropped successfully!' % name, 'success')
            return redirect(url_for('table_structure', table=table))
        else:
            flash('Trigger name is required.', 'danger')

    return render_template(
        'drop_trigger.html',
        triggers=triggers,
        trigger_names=trigger_names,
        name=name,
        table=table)

@app.route(prefix+'/<table>/content/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_table_content(table):
    page_number = request.args.get('page') or ''
    page_number = int(page_number) if page_number.isdigit() else 1
    dataset = dataSetCache.dataset
    dataset.update_cache(table)
    ds_table = dataset[table]
    total_rows = ds_table.all().count()
    #ROWS_PER_PAGE = app.config['ROWS_PER_PAGE']
    total_pages = int(math.ceil(total_rows / float(ROWS_PER_PAGE)))
    # Restrict bounds.
    page_number = min(page_number, total_pages)
    page_number = max(page_number, 1)

    previous_page = page_number - 1 if page_number > 1 else None
    next_page = page_number + 1 if page_number < total_pages else None

    query = ds_table.all().paginate(page_number, ROWS_PER_PAGE)

    ordering = request.args.get('ordering')
    if ordering:
        field = ds_table.model_class._meta.columns[ordering.lstrip('-')]
        if ordering.startswith('-'):
            field = field.desc()
        query = query.order_by(field)

    field_names = ds_table.columns
    columns = [f.column_name for f in ds_table.model_class._meta.sorted_fields]

    table_sql = dataset.query(
        'SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type = ?',
        [table, 'table']).fetchone()[0]

    return render_template(
        'table_content.html',
        columns=columns,
        ds_table=ds_table,
        field_names=field_names,
        next_page=next_page,
        ordering=ordering,
        page=page_number,
        previous_page=previous_page,
        query=query,
        table=table,
        total_pages=total_pages,
        total_rows=total_rows)

@app.route(prefix+'/<table>/query/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_table_query(table):
    data = []
    data_description = error = row_count = sql = None
    dataset = dataSetCache.dataset
    if request.method == 'POST':
        sql = request.form['sql']
        if 'export_json' in request.form:
            return export(table, sql, 'json')
        elif 'export_csv' in request.form:
            return export(table, sql, 'csv')

        try:
            cursor = dataset.query(sql)
        except Exception as exc:
            error = str(exc)
        else:
            #MAX_RESULT_SIZE = app.config['MAX_RESULT_SIZE']
            data = cursor.fetchall()[:MAX_RESULT_SIZE]
            data_description = cursor.description
            row_count = cursor.rowcount
    else:
        if request.args.get('sql'):
            sql = request.args.get('sql')
        else:
            sql = 'SELECT *\nFROM "%s"' % (table)

    table_sql = dataset.query(
        'SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type = ?',
        [table, 'table']).fetchone()[0]

    return render_template(
        'table_query.html',
        data=data,
        data_description=data_description,
        error=error,
        query_images=get_query_images(),
        row_count=row_count,
        sql=sql,
        table=table,
        table_sql=table_sql)

@app.route(prefix+'/table-definition/', methods=['POST'])
def pysqliteadmin_set_table_definition_preference():
    if 'pysqliteadmin-db-id' not in session: return redirect('/soft')
    key = 'show'
    show = False
    if request.form.get(key) and request.form.get(key) != 'false':
        session[key] = show = True
    elif key in session:
        del session[key]
    return jsonify({key: show})

def export(table, sql, export_format):
    dataset = dataSetCache.dataset
    model_class = dataset[table].model_class
    query = model_class.raw(sql).dicts()
    buf = StringIO()
    if export_format == 'json':
        kwargs = {'indent': 2}
        filename = '%s-export.json' % table
        mimetype = 'text/javascript'
    else:
        kwargs = {}
        filename = '%s-export.csv' % table
        mimetype = 'text/csv'

    dataset.freeze(query, export_format, file_obj=buf, **kwargs)

    response_data = buf.getvalue()
    response = make_response(response_data)
    response.headers['Content-Length'] = len(response_data)
    response.headers['Content-Type'] = mimetype
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % (
        filename)
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'public'
    return response

@app.route(prefix+'/<table>/import/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_table_import(table):
    count = None
    request_data = get_request_data()
    strict = bool(request_data.get('strict'))
    dataset = dataSetCache.dataset
    if request.method == 'POST':
        file_obj = request.files.get('file')
        if not file_obj:
            flash('Please select an import file.', 'danger')
        elif not file_obj.filename.lower().endswith(('.csv', '.json')):
            flash('Unsupported file-type. Must be a .json or .csv file.',
                  'danger')
        else:
            if file_obj.filename.lower().endswith('.json'):
                format = 'json'
            else:
                format = 'csv'
            try:
                with dataset.transaction():
                    count = dataset.thaw(
                        table,
                        format=format,
                        file_obj=file_obj.stream,
                        strict=strict)
            except Exception as exc:
                flash('Error importing file: %s' % exc, 'danger')
            else:
                flash(
                    'Successfully imported %s objects from %s.' % (
                        count, file_obj.filename),
                    'success')
                return redirect(url_for('table_content', table=table))

    return render_template(
        'table_import.html',
        count=count,
        strict=strict,
        table=table)

@app.route(prefix+'/<table>/drop/', methods=['GET', 'POST'])
@require_table
def pysqliteadmin_drop_table(table):
    dataset = dataSetCache.dataset
    if request.method == 'POST':
        model_class = dataset[table].model_class
        model_class.drop_table()
        flash('Table "%s" dropped successfully.' % table, 'success')
        return redirect(url_for('index'))

    return render_template('drop_table.html', table=table)


############################################################

#@app.route('/pysqliteadmin/static/<filename:re:.*>')
@app.route(prefix+'/static/<filename>', methods=['GET', 'POST'])
def pysqliteadmin_static(filename):
    #if filename.endswith('.map'): filename=filename[:-4]
    #这个route没有用
    return static_file('static/'+filename,root = basedir)






def scan_sqlite3(sPath, exts='*.*', callback=None):
    rs = []
    if isinstance(exts, str):
        _exts = exts.replace('.','[.]').replace('*','.*').replace(';','|').strip('|')
        _exts = '('+_exts+')'+'$'
           
    for root, dirs, files in os.walk(sPath, True, None, False):     
        for f in files:
            fpath = os.path.join(root,f)
            if not os.path.isfile(fpath):  continue
            if isinstance(exts, str):
                if '*.*' not in exts:
                    if not re.match(_exts, f, flags=re.I): continue #match
            else:
                ext = os.path.splitext(f)[1].lower() 
                if ext not in exts: continue
                
            fp=open(fpath, 'rb')
            words = fp.read(15)
            fp.close()
            if words!= b'SQLite format 3': continue
            rs.append(fpath)
            if callback: callback(fpath)
            #print(fpath)
    return rs


    
    








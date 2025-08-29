-- Trigger function to process alerts when a new signal is inserted
create or replace function process_alerts()
returns trigger as $$
declare
    alert_record record;
begin
    -- Loop through all active alerts
    for alert_record in
        select * from alerts where is_active = true
    loop
        -- Check if the new signal matches the alert filters
        if (alert_record.filters->'symbols' is null or new.symbol = any (array(select jsonb_array_elements_text(alert_record.filters->'symbols'))))
        and (alert_record.filters->'timeframes' is null or new.timeframe = any (array(select jsonb_array_elements_text(alert_record.filters->'timeframes'))))
        and (alert_record.filters->'signalCodes' is null or new.signal_codes @> array(select jsonb_array_elements_text(alert_record.filters->'signalCodes')))
        then
            -- Insert into a notifications table (to be created later) or handle notification logic
            insert into notifications(user_id, signal_id, created_at)
            values (alert_record.user_id, new.signal_id, now());
        end if;
    end loop;
    return new;
end;
$$ language plpgsql;

-- Create trigger on signals table
drop trigger if exists trg_process_alerts on signals;
create trigger trg_process_alerts
after insert on signals
for each row
execute function process_alerts();
